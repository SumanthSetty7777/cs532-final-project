from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict

from app.core.request_types import InferenceResult


class ResultNotFoundError(KeyError):
    """Raised when a request_id is not registered in the result store."""


class ResultTimeoutError(TimeoutError):
    """Raised when waiting for a result times out."""


@dataclass
class _PendingResult:
    """
    Internal container for one request's completion event and final result.
    """
    event: threading.Event
    result: InferenceResult | None = None


class ResultStore:
    """
    Thread-safe store for tracking pending and completed inference results.

    Flow:
      - API registers request_id via create_pending()
      - worker calls set_result()
      - API waits using wait_for_result()
      - API cleans up via cleanup()
    """

    def __init__(self) -> None:
        self._store: Dict[str, _PendingResult] = {}
        self._lock = threading.Lock()

    def create_pending(self, request_id: str) -> None:
        """
        Register a request as pending.

        Raises:
            ValueError: if request_id already exists.
        """
        with self._lock:
            if request_id in self._store:
                raise ValueError(f"request_id '{request_id}' is already registered")
            self._store[request_id] = _PendingResult(event=threading.Event())

    def set_result(self, result: InferenceResult) -> None:
        """
        Store the completed result and notify any waiting thread.

        Raises:
            ResultNotFoundError: if request_id is not known.
        """
        with self._lock:
            pending = self._store.get(result.request_id)
            if pending is None:
                raise ResultNotFoundError(
                    f"request_id '{result.request_id}' not found in ResultStore"
                )

            pending.result = result
            pending.event.set()

    def wait_for_result(self, request_id: str, timeout: float) -> InferenceResult:
        """
        Wait until the result for request_id is available.

        Args:
            request_id: ID of the request to wait for.
            timeout: max time in seconds to wait.

        Returns:
            InferenceResult

        Raises:
            ResultNotFoundError: if request_id was never registered.
            ResultTimeoutError: if the result does not arrive in time.
            RuntimeError: if event is set but result is unexpectedly missing.
        """
        with self._lock:
            pending = self._store.get(request_id)
            if pending is None:
                raise ResultNotFoundError(
                    f"request_id '{request_id}' not found in ResultStore"
                )

            event = pending.event

        completed = event.wait(timeout=timeout)
        if not completed:
            raise ResultTimeoutError(
                f"Timed out waiting for result for request_id '{request_id}'"
            )

        with self._lock:
            pending = self._store.get(request_id)
            if pending is None:
                raise ResultNotFoundError(
                    f"request_id '{request_id}' disappeared during wait"
                )
            if pending.result is None:
                raise RuntimeError(
                    f"request_id '{request_id}' signaled completion but no result exists"
                )
            return pending.result

    def get_result_if_ready(self, request_id: str) -> InferenceResult | None:
        """
        Return the result immediately if ready, else None.

        Raises:
            ResultNotFoundError: if request_id is not registered.
        """
        with self._lock:
            pending = self._store.get(request_id)
            if pending is None:
                raise ResultNotFoundError(
                    f"request_id '{request_id}' not found in ResultStore"
                )
            return pending.result

    def cleanup(self, request_id: str) -> None:
        """
        Remove request tracking information from the store.

        Safe to call after the API returns a response.
        """
        with self._lock:
            self._store.pop(request_id, None)

    def size(self) -> int:
        """
        Number of request entries currently tracked.
        """
        with self._lock:
            return len(self._store)
