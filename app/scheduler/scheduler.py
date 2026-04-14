from __future__ import annotations

import threading
import time
from queue import Empty
from typing import List

from app.core.request_types import InferenceRequest
from app.queueing.request_queue import RequestQueue
from app.workers.worker_pool import WorkerPool


class Scheduler:
    """
    Background scheduler that forms static batches from the request queue
    and submits them to the worker pool.

    Mid-project behavior:
    - wait for first request
    - collect up to batch_size requests
    - stop collecting when max_wait_s expires
    - submit batch to worker pool
    """

    def __init__(
        self,
        request_queue: RequestQueue,
        worker_pool: WorkerPool,
        batch_size: int,
        max_wait_s: float,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if max_wait_s < 0:
            raise ValueError("max_wait_s must be >= 0")

        self.request_queue = request_queue
        self.worker_pool = worker_pool
        self.batch_size = batch_size
        self.max_wait_s = max_wait_s

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self.run_loop, daemon=True)

    def start(self) -> None:
        if self._thread.is_alive():
            return
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=1.0)

    def run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                first_request = self.request_queue.get_next(timeout=0.5)
            except Empty:
                continue

            batch = self._build_batch(first_request)
            if batch:
                print(f"[Scheduler] Dispatching batch of size {len(batch)}")
                self.worker_pool.submit_batch(batch)

    def _build_batch(self, first_request: InferenceRequest) -> List[InferenceRequest]:
        """
        Build a batch starting with the first request.

        Then keep collecting until:
        - batch_size is reached, or
        - max_wait_s expires
        """
        batch = [first_request]

        if len(batch) >= self.batch_size:
            return batch

        deadline = time.time() + self.max_wait_s

        while len(batch) < self.batch_size and not self._stop_event.is_set():
            remaining = deadline - time.time()
            if remaining <= 0:
                break

            try:
                next_request = self.request_queue.get_next(timeout=remaining)
                batch.append(next_request)
            except Empty:
                break

        return batch
