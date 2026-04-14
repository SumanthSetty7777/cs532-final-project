from __future__ import annotations

import queue
import threading
from typing import List

from app.core.request_types import InferenceRequest
from app.core.result_store import ResultStore
from app.model.inference import ModelRunner
from app.workers.worker import Worker


class WorkerPool:
    """
    Manages worker threads and a shared batch queue.
    The scheduler submits batches to this pool.
    """

    def __init__(
        self,
        num_workers: int,
        result_store: ResultStore,
        model_runner: ModelRunner,
        batch_queue_size: int = 0,
    ) -> None:
        self.num_workers = num_workers
        self.result_store = result_store
        self.model_runner = model_runner
        self.batch_queue: queue.Queue[List[InferenceRequest]] = queue.Queue(
            maxsize=batch_queue_size
        )
        self.stop_event = threading.Event()
        self.workers: list[Worker] = []

    def start(self) -> None:
        if self.workers:
            return

        for worker_id in range(self.num_workers):
            worker = Worker(
                worker_id=worker_id,
                batch_queue=self.batch_queue,
                result_store=self.result_store,
                model_runner=self.model_runner,
                stop_event=self.stop_event,
            )
            worker.start()
            self.workers.append(worker)

    def submit_batch(self, batch: List[InferenceRequest]) -> None:
        if not batch:
            return
        self.batch_queue.put(batch)

    def stop(self) -> None:
        self.stop_event.set()

        for worker in self.workers:
            worker.join(timeout=1.0)

    def pending_batches(self) -> int:
        return self.batch_queue.qsize()
