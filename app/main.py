from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.config import RESULT_TIMEOUT_SECONDS
from app.core.request_types import create_inference_request
from app.core.result_store import ResultNotFoundError, ResultTimeoutError
from app.core.startup import get_system_context, shutdown_system, startup_system
from app.schemas import PredictRequest, PredictResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_system()
    try:
        yield
    finally:
        shutdown_system()


app = FastAPI(title="ML Inference Serving System", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    system = get_system_context()

    request_id = str(uuid.uuid4())
    inference_request = create_inference_request(
        request_id=request_id,
        text=request.text,
    )

    system.result_store.create_pending(request_id)

    try:
        system.request_queue.submit(inference_request)

        result = system.result_store.wait_for_result(
            request_id=request_id,
            timeout=RESULT_TIMEOUT_SECONDS,
        )

        latency_ms = (result.completed_at - inference_request.created_at) * 1000.0

        return PredictResponse(
            request_id=request_id,
            output=str(result.output),
            latency_ms=round(latency_ms, 3),
        )

    except ResultTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except ResultNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        system.result_store.cleanup(request_id)
