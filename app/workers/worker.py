from __future__ import annotations

import queue
import threading
import time
from typing import List

from app.core.request_types import InferenceRequest, InferenceResult
from app.core.result_store import ResultStore
from app.model.inference import ModelRunner


class Worker(threading.Thread):
    """
    Worker thread that consumes batches from a shared batch queue,
    runs inference, and stores results in the ResultStore.
    """

    def __init__(
        self,
        worker_id: int,
        batch_queue: queue.Queue[List[InferenceRequest]],
        result_store: ResultStore,
        model_runner: ModelRunner,
        stop_event: threading.Event,
    ) -> None:
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.batch_queue = batch_queue
        self.result_store = result_store
        self.model_runner = model_runner
        self.stop_event = stop_event

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                batch = self.batch_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self._process_batch(batch)
            finally:
                self.batch_queue.task_done()

    def _process_batch(self, batch: List[InferenceRequest]) -> None:
        print(f"[Worker {self.worker_id}] Processing batch of size {len(batch)}")
        
        texts = [req.text for req in batch]
        outputs = self.model_runner.run_batch(texts)

        if len(outputs) != len(batch):
            raise RuntimeError(
                f"Worker {self.worker_id}: output count {len(outputs)} "
                f"does not match batch size {len(batch)}"
            )

        completed_at = time.time()
        for req, output in zip(batch, outputs):
            result = InferenceResult(
                request_id=req.request_id,
                output=output,
                completed_at=completed_at,
            )
            self.result_store.set_result(result)
