# cs532-final-project
Scalable ML inference system with batching, scheduling, and worker-based execution.

# ML Inference Serving System

This project implements a scalable machine learning inference system designed to handle incoming prediction requests efficiently under varying workloads.

The system focuses on **systems design for ML inference**, including batching, scheduling, and concurrent request handling, rather than model training or accuracy.

## 🚀 Overview

The architecture follows a typical ML serving pipeline:

Client → API → Queue → Scheduler → Worker Pool → Model → Response

- API receives inference requests
- Requests are stored in a shared queue
- A scheduler forms batches of requests
- Worker threads process batches using a model
- Results are returned to the client

## 🎯 Key Features

- Request queue for handling concurrent inputs
- Static batching (mid-project)
- Worker pool for parallel processing
- Scheduler for batch formation
- End-to-end request handling with response mapping

## 📊 Future Enhancements (Final Phase)

- Dynamic batching based on system load
- Priority-based scheduling
- Backpressure handling under overload
- Performance metrics (latency, throughput, queue size)
- Load testing and evaluation

## 🛠️ Tech Stack

- Python
- FastAPI
- Threading / Concurrency
- PyTorch / Hugging Face (for inference)

## 📁 Project Structure
client/
  main.py # simple request client
  image_input.py # sends dog.jpeg as a base64 image request
  dog.jpeg # sample image for demo/testing

leader/
  main.py # FastAPI leader/API server, batching, worker registry, heartbeats
  send_inference.py # chooses a worker and sends a batch
  add_worker.py # worker state object and registration helper
  input_object.py # request wrapper with unique id
  utilities/unique_id.py # UUID helper

follower/
  main.py # FastAPI worker process
  inference.py # loads ResNet-18 and runs image inference
  heartbeat.py # worker registration and heartbeat loop

tests/
  testsuite.py # integration tests placeholder
  load_test.py # concurrent load generator and worker-scaling experiment runner

results/
  load_test_*.csv # generated load-test measurements


## 👥 Team 
- Brody Massad  
- Hung Truong 
- Ipsita Bhattacharjee  
- Sumanth Setty 

## ⚙️ Setup

Create or activate the project virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ▶️ Running Locally

Start the leader in terminal 1:

```bash
cd /Users/ssetty/Documents/sys_dl/Project_test/cs532-final-project
source .venv/bin/activate
cd leader
uvicorn main:app --host 127.0.0.1 --port 8000
```

Start one worker in terminal 2:

```bash
cd /Users/ssetty/Documents/sys_dl/Project_test/cs532-final-project
source .venv/bin/activate
cd follower
python main.py 8001
```

Send the sample image request in terminal 3:

```bash
cd /Users/ssetty/Documents/sys_dl/Project_test/cs532-final-project
source .venv/bin/activate
cd client
python image_input.py
```

Expected output:

```text
200
{'id': '...', 'output': 'golden retriever', 'isError': False}
```

Additional workers can be started on new ports:

```bash
cd follower
python main.py 8002
```

## 📈 Load Testing

With the leader and at least one worker running, run:

```bash
cd /Users/ssetty/Documents/sys_dl/Project_test/cs532-final-project
source .venv/bin/activate
python tests/load_test.py --requests 20 --concurrency 5
```

The script prints a summary and writes per-request results to a CSV in `results/`.
Use `--verbose` if you want to print every request line in the terminal.
Useful experiment knobs:

```bash
python tests/load_test.py --requests 10 --concurrency 2
python tests/load_test.py --requests 25 --concurrency 5
python tests/load_test.py --requests 50 --concurrency 10
```

The load tester can also use a folder of images:

```bash
python tests/load_test.py --image-dir data/imagewoof2-160/val --requests 100 --concurrency 10
```

Recommended datasets for ResNet-18 load testing:

- Imagewoof 160px: small ImageNet subset with dog breeds, good for this image-classification demo.
- Imagenette 160px: small ImageNet subset with 10 easy classes, good if you want more varied objects.
- Oxford-IIIT Pet: available through torchvision, useful if you want a cat/dog dataset without adding new libraries.

Example Imagewoof download:

```bash
mkdir -p data
curl -L https://s3.amazonaws.com/fast-ai-imageclas/imagewoof2-160.tgz -o data/imagewoof2-160.tgz
tar -xzf data/imagewoof2-160.tgz -C data
python tests/load_test.py --image-dir data/imagewoof2-160/val --requests 100 --concurrency 10
```

Example Imagenette download:

```bash
mkdir -p data
curl -L https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-160.tgz -o data/imagenette2-160.tgz
tar -xzf data/imagenette2-160.tgz -C data
python tests/load_test.py --image-dir data/imagenette2-160/val --requests 100 --concurrency 10
```

## ⚖️ Worker Scaling Experiment

Stop any manually running leader/workers first, then run:

```bash
cd /Users/ssetty/Documents/sys_dl/Project_test/cs532-final-project
source .venv/bin/activate
python tests/load_test.py --image-dir data/imagewoof2-160/val --workers 1,2,3 --requests 50 --concurrency 10
```

This script runs the same load test with 1 worker, then 2 workers, then 3 workers. It writes per-run CSVs plus a `summary.csv` under `results/worker_scaling_<timestamp>/`.

## 📌 Notes
This project is part of **COMPSCI 532: Systems for Data Science** at UMass Amherst.
