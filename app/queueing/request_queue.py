from __future__ import annotations

from queue import Empty, Full, Queue
from typing import Optional

from app.core.request_types import InferenceRequest


class RequestQueue:
    """
    Thread-safe queue for storing incoming inference requests.

    This wraps Python's built-in Queue so the rest of the code depends on
    our interface rather than directly on queue.Queue.
    """

    def __init__(self, max_size: int = 0) -> None:
        """
        Args:
            max_size:
                Maximum number of items allowed in the queue.
                0 means unbounded.
        """
        self._queue: Queue[InferenceRequest] = Queue(maxsize=max_size)

    def submit(self, request: InferenceRequest) -> None:
        """
        Add a request to the queue. Blocks if the queue is full.
        """
        self._queue.put(request)

    def submit_nowait(self, request: InferenceRequest) -> bool:
        """
        Try to add a request without blocking.

        Returns:
            True if request was added, False if queue is full.
        """
        try:
            self._queue.put_nowait(request)
            return True
        except Full:
            return False

    def get_next(self, timeout: Optional[float] = None) -> InferenceRequest:
        """
        Get the next request from the queue.

        Args:
            timeout:
                Number of seconds to wait before raising queue.Empty.
                If None, block until an item is available.

        Raises:
            queue.Empty: if no item becomes available within timeout.
        """
        return self._queue.get(timeout=timeout)

    def get_nowait(self) -> InferenceRequest:
        """
        Get the next request immediately.

        Raises:
            queue.Empty: if the queue is empty.
        """
        return self._queue.get_nowait()

    def task_done(self) -> None:
        """
        Mark a formerly enqueued task as complete.

        Useful if you later want to use Queue.join().
        """
        self._queue.task_done()

    def size(self) -> int:
        """
        Current approximate queue size.
        """
        return self._queue.qsize()

    def is_empty(self) -> bool:
        """
        Return True if the queue is currently empty.
        """
        return self._queue.empty()

    def is_full(self) -> bool:
        """
        Return True if the queue is currently full.
        """
        return self._queue.full()
