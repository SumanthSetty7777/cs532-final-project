from __future__ import annotations

from dataclasses import dataclass

from app.config import (
    BATCH_SIZE,
    MAX_WAIT_SECONDS,
    NUM_WORKERS,
    REQUEST_QUEUE_MAX_SIZE,
    WORKER_BATCH_QUEUE_MAX_SIZE,
)
from app.core.result_store import ResultStore
from app.model.inference import ModelRunner
from app.queueing.request_queue import RequestQueue
from app.scheduler.scheduler import Scheduler
from app.workers.worker_pool import WorkerPool


@dataclass
class SystemContext:
    request_queue: RequestQueue
    result_store: ResultStore
    model_runner: ModelRunner
    worker_pool: WorkerPool
    scheduler: Scheduler


_system_context: SystemContext | None = None


def create_system_context() -> SystemContext:
    request_queue = RequestQueue(max_size=REQUEST_QUEUE_MAX_SIZE)
    result_store = ResultStore()
    model_runner = ModelRunner()

    worker_pool = WorkerPool(
        num_workers=NUM_WORKERS,
        result_store=result_store,
        model_runner=model_runner,
        batch_queue_size=WORKER_BATCH_QUEUE_MAX_SIZE,
    )

    scheduler = Scheduler(
        request_queue=request_queue,
        worker_pool=worker_pool,
        batch_size=BATCH_SIZE,
        max_wait_s=MAX_WAIT_SECONDS,
    )

    return SystemContext(
        request_queue=request_queue,
        result_store=result_store,
        model_runner=model_runner,
        worker_pool=worker_pool,
        scheduler=scheduler,
    )


def get_system_context() -> SystemContext:
    global _system_context
    if _system_context is None:
        raise RuntimeError("System context has not been initialized")
    return _system_context


def startup_system() -> SystemContext:
    global _system_context
    if _system_context is not None:
        return _system_context

    _system_context = create_system_context()
    _system_context.worker_pool.start()
    _system_context.scheduler.start()
    return _system_context


def shutdown_system() -> None:
    global _system_context
    if _system_context is None:
        return

    _system_context.scheduler.stop()
    _system_context.worker_pool.stop()
    _system_context = None
