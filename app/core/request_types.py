from dataclasses import dataclass
from typing import Any
import time


@dataclass(slots=True)
class InferenceRequest:
    """
    Internal request object that flows through the system.
    """
    request_id: str
    text: str
    created_at: float


@dataclass(slots=True)
class InferenceResult:
    """
    Result produced by the worker and stored for the API to retrieve.
    """
    request_id: str
    output: Any
    completed_at: float


def create_inference_request(request_id: str, text: str) -> InferenceRequest:
    """
    Helper to create a request with the current timestamp.
    """
    return InferenceRequest(
        request_id=request_id,
        text=text,
        created_at=time.time(),
    )