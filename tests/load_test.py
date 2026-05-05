# Load test helper for the leader/follower inference system.
# It can test an already-running leader, or start fresh leaders/workers itself.
# The CSV output is meant for the report and graphs, while terminal output stays short.
import argparse
import base64
import csv
import os
import socket
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from itertools import cycle
from pathlib import Path

import requests


# Keep default paths relative to the repo, so the script works even if it is run
# from a different current directory.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
LEADER_DIR = PROJECT_DIR / "leader"
FOLLOWER_DIR = PROJECT_DIR / "follower"
DEFAULT_IMAGE = PROJECT_DIR / "client" / "dog.jpeg"
RESULTS_DIR = PROJECT_DIR / "results"


# Treat relative CLI paths as repo-relative paths.
def resolve_project_path(path):
    if not path:
        return ""
    path_obj = Path(path)
    if path_obj.is_absolute():
        return str(path_obj)
    return str(PROJECT_DIR / path_obj)


# Convert an image file into the format expected by the inference API.
def image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# Use either one image or all images inside a dataset folder.
def collect_image_paths(image_path, image_dir):
    if image_dir:
        image_paths = []
        for root, _, files in os.walk(image_dir):
            for filename in files:
                if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    image_paths.append(os.path.join(root, filename))
        return sorted(image_paths)
    return [image_path]


# Build the same JSON shape used by the normal client.
def build_payload(image_path):
    return {
        "data": {
            "image_base64": image_to_base64(image_path),
        }
    }


# Send one request and return one CSV-ready result row.
def send_request(server_url, image_path, request_num, timeout):
    start = time.perf_counter()
    try:
        payload = build_payload(image_path)
        response = requests.post(
            f"{server_url}/inference",
            json=payload,
            timeout=timeout,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        try:
            body = response.json()
        except ValueError:
            body = {"raw_body": response.text}

        return {
            "request_num": request_num,
            "image_path": image_path,
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 3),
            "request_id": body.get("id", ""),
            "output": body.get("output", body.get("error", "")),
            "is_error": body.get("isError", response.status_code >= 400),
        }
    except requests.RequestException as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "request_num": request_num,
            "image_path": image_path,
            "status_code": "",
            "latency_ms": round(latency_ms, 3),
            "request_id": "",
            "output": str(exc),
            "is_error": True,
        }


# Write per-request results so we can inspect failures or graph latencies.
def write_csv(path, rows):
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "request_num",
        "image_path",
        "status_code",
        "latency_ms",
        "request_id",
        "output",
        "is_error",
    ]
    with open(path_obj, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# A request only counts as successful if HTTP and the app both say it worked.
def row_succeeded(row):
    is_error = str(row["is_error"]).lower() in ("true", "1", "yes")
    return str(row["status_code"]) == "200" and not is_error


# Calculate percentiles without needing numpy or pandas.
def percentile(values, pct):
    if not values:
        return ""
    values = sorted(values)
    index = (len(values) - 1) * (pct / 100)
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    if lower == upper:
        return values[lower]
    weight = index - lower
    return values[lower] * (1 - weight) + values[upper] * weight


# Collapse raw request rows into the metrics we discuss in the report.
def summarize_rows(rows, elapsed_sec, csv_path, worker_count=""):
    successful = [row for row in rows if row_succeeded(row)]
    latencies = [float(row["latency_ms"]) for row in successful]

    return {
        "workers": worker_count,
        "total_requests": len(rows),
        "successful": len(successful),
        "failed": len(rows) - len(successful),
        "elapsed_sec": round(elapsed_sec, 3),
        "throughput_req_per_sec": round(len(rows) / elapsed_sec, 3) if elapsed_sec > 0 else "",
        "latency_avg_ms": round(statistics.mean(latencies), 3) if latencies else "",
        "latency_p50_ms": round(percentile(latencies, 50), 3) if latencies else "",
        "latency_p95_ms": round(percentile(latencies, 95), 3) if latencies else "",
        "latency_min_ms": round(min(latencies), 3) if latencies else "",
        "latency_max_ms": round(max(latencies), 3) if latencies else "",
        "csv_path": str(csv_path),
    }


# Print a compact key/value summary for a single load-test run.
def print_summary(summary):
    for key in [
        "workers",
        "total_requests",
        "successful",
        "failed",
        "elapsed_sec",
        "throughput_req_per_sec",
        "latency_avg_ms",
        "latency_p50_ms",
        "latency_p95_ms",
        "latency_min_ms",
        "latency_max_ms",
        "csv_path",
    ]:
        if summary[key] != "":
            print(f"{key}: {summary[key]}")


# Run the client-side load test using a pool of concurrent request threads.
def run_client_load(
    server_url,
    image_path,
    image_dir,
    request_count,
    concurrency,
    timeout,
    csv_path,
    worker_count="",
    verbose=False,
    print_run_summary=True,
):
    image_paths = collect_image_paths(image_path, image_dir)
    if not image_paths:
        raise ValueError("No images found. Use --image or --image-dir with .jpg/.jpeg/.png files.")

    print(
        f"Running {request_count} requests with concurrency={concurrency} "
        f"using {len(image_paths)} image(s)."
    )

    # If there are fewer images than requests, cycle through the images. This
    # lets us test with one dog image or a full dataset using the same code.
    selected_images = []
    for _, selected_image in zip(range(request_count), cycle(image_paths)):
        selected_images.append(selected_image)

    start = time.perf_counter()
    rows = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(send_request, server_url, selected_image, i + 1, timeout)
            for i, selected_image in enumerate(selected_images)
        ]
        # as_completed gives results as soon as each request finishes. We sort
        # later so the CSV is still in request number order.
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            if verbose:
                print(
                    f"request={row['request_num']} status={row['status_code']} "
                    f"latency_ms={row['latency_ms']} image={os.path.basename(row['image_path'])} "
                    f"output={row['output']}"
                )

    elapsed_sec = time.perf_counter() - start
    rows.sort(key=lambda row: row["request_num"])
    write_csv(csv_path, rows)

    summary = summarize_rows(rows, elapsed_sec, csv_path, worker_count=worker_count)
    if print_run_summary:
        print_summary(summary)
    return summary


# Convert a string like '1,3,5' into worker counts for scaling tests.
def parse_worker_counts(raw_counts):
    if not raw_counts:
        return []

    counts = []
    for value in raw_counts.split(","):
        value = value.strip()
        if value:
            counts.append(int(value))

    if not counts or any(count <= 0 for count in counts):
        raise ValueError("--workers must contain positive integers, e.g. 1,2,3")
    return counts


# Check whether a local port is already occupied before starting servers.
def port_is_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


# Fail early if an old leader/worker is still running on the needed ports.
def ensure_ports_free(ports):
    busy_ports = [port for port in ports if port_is_open(port)]
    if busy_ports:
        raise RuntimeError(
            "Ports already in use: "
            + ", ".join(str(port) for port in busy_ports)
            + ". Stop existing leader/worker terminals or choose different ports."
        )


# Start a leader or worker process and save its output to a log file.
def start_process(cmd, cwd, log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "w")
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log_file.close()
    return process


# Wait until the leader is reachable before starting workers.
def wait_for_http(url, timeout_sec):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code < 500:
                return
        except requests.RequestException:
            pass
        time.sleep(0.25)
    raise TimeoutError(f"Timed out waiting for {url}")


# Shut down started processes even if the load test fails halfway through.
def terminate_processes(processes):
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()

    for process in reversed(processes):
        if process.poll() is None:
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


# Save one row per worker count so scaling results are easy to graph.
def write_scaling_summary(run_dir, summaries):
    summary_path = run_dir / "summary.csv"
    fieldnames = [
        "workers",
        "total_requests",
        "successful",
        "failed",
        "elapsed_sec",
        "throughput_req_per_sec",
        "latency_avg_ms",
        "latency_p50_ms",
        "latency_p95_ms",
        "latency_min_ms",
        "latency_max_ms",
        "csv_path",
    ]
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    return summary_path


# Print a copy-friendly table after all worker-count experiments finish.
def print_scaling_table(summaries):
    print("\nWorker scaling summary")
    print("workers,total,success,failed,throughput,avg_ms,p50_ms,p95_ms")
    for row in summaries:
        print(
            f"{row['workers']},{row['total_requests']},{row['successful']},"
            f"{row['failed']},{row['throughput_req_per_sec']},"
            f"{row['latency_avg_ms']},{row['latency_p50_ms']},{row['latency_p95_ms']}"
        )


# Start one clean leader/worker setup, run the test, then clean it up.
def run_worker_experiment(args, worker_count, run_dir):
    worker_ports = [args.first_worker_port + idx for idx in range(worker_count)]
    ensure_ports_free([args.leader_port] + worker_ports)

    processes = []
    logs_dir = run_dir / "logs"
    leader_url = f"http://localhost:{args.leader_port}"

    try:
        print(f"\n=== Starting experiment with {worker_count} worker(s) ===")
        leader = start_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(args.leader_port),
            ],
            LEADER_DIR,
            logs_dir / f"leader_workers_{worker_count}.log",
        )
        processes.append(leader)
        wait_for_http(f"{leader_url}/docs", timeout_sec=args.leader_startup_timeout)

        # Workers register with the leader when they start. The extra wait gives
        # each worker time to load the model before we begin measuring latency.
        for port in worker_ports:
            worker = start_process(
                [sys.executable, "main.py", str(port)],
                FOLLOWER_DIR,
                logs_dir / f"worker_{port}_workers_{worker_count}.log",
            )
            processes.append(worker)

        print(f"Waiting {args.worker_startup_wait}s for worker model loading and registration...")
        time.sleep(args.worker_startup_wait)

        csv_path = run_dir / f"workers_{worker_count}.csv"
        return run_client_load(
            leader_url,
            args.image,
            args.image_dir,
            args.requests,
            args.concurrency,
            args.timeout,
            csv_path,
            worker_count=worker_count,
            verbose=args.verbose,
            print_run_summary=False,
        )
    finally:
        terminate_processes(processes)
        time.sleep(args.between_runs_wait)


# Run the same load test repeatedly with different numbers of workers.
def run_worker_scaling(args, worker_counts):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out_dir) if args.out_dir else RESULTS_DIR / f"worker_scaling_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for worker_count in worker_counts:
        summaries.append(run_worker_experiment(args, worker_count, run_dir))

    summary_path = write_scaling_summary(run_dir, summaries)
    print_scaling_table(summaries)
    print(f"\nsummary_csv: {summary_path}")


# Parse CLI arguments and choose either normal mode or worker-scaling mode.
def main():
    parser = argparse.ArgumentParser(description="Concurrent load test for the inference leader.")
    parser.add_argument("--server-url", default="http://localhost:8000")
    parser.add_argument("--image", default=str(DEFAULT_IMAGE))
    parser.add_argument("--image-dir", default="")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--csv", default="")
    parser.add_argument("--workers", default="")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--leader-port", type=int, default=8000)
    parser.add_argument("--first-worker-port", type=int, default=8001)
    parser.add_argument("--leader-startup-timeout", type=float, default=20)
    parser.add_argument("--worker-startup-wait", type=float, default=12)
    parser.add_argument("--between-runs-wait", type=float, default=2)
    parser.add_argument("--out-dir", default="")
    args = parser.parse_args()

    args.image = resolve_project_path(args.image)
    args.image_dir = resolve_project_path(args.image_dir)
    if args.out_dir:
        args.out_dir = resolve_project_path(args.out_dir)

    worker_counts = parse_worker_counts(args.workers)
    if worker_counts:
        # Scaling mode owns the leader/workers itself.
        run_worker_scaling(args, worker_counts)
        return

    csv_path = args.csv
    if csv_path:
        csv_path = resolve_project_path(csv_path)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = RESULTS_DIR / f"load_test_{timestamp}.csv"

    # Normal mode assumes the leader and workers are already running.
    run_client_load(
        args.server_url,
        args.image,
        args.image_dir,
        args.requests,
        args.concurrency,
        args.timeout,
        csv_path,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
