# runs on each follower/worker machine
# leader sends this worker batches of inference inputs

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, List
import threading
import sys
from inference import load_model, inference_batch
from heartbeat import connect_to_leader, heartbeat_loop


app = FastAPI()

LEADER_URL = "http://localhost:8000"

# this follower's addr; leader stores this + uses it to call this worker's /inference route
MY_ADDR = "http://localhost:"

MY_PORT = int(sys.argv[1])

# load model once when follower starts
model = load_model()


class InferenceItem(BaseModel):
    # ID created by leader/cli so outputs can be matched back correctly
    id: str

    # the actual input obj for the model
    input: Any


class InferenceResult(BaseModel):
    # same ID as the input item
    id: str

    # model output OR None (if smt failed)
    output: Any = None

    # True means item failed during inference
    isError: bool


@app.on_event("startup")
def startup_event():
    worker_addr = MY_ADDR + str(MY_PORT)

    # tell leader this worker exists
    connect_to_leader(LEADER_URL, worker_addr)

    # keep telling leader this worker is alive
    thread = threading.Thread(
        target=heartbeat_loop,
        args=(LEADER_URL, MY_ADDR + str(MY_PORT)),
        daemon=True
    )
    thread.start()


@app.post("/inference", response_model=List[InferenceResult])
def run_inference(items: List[InferenceItem]):
    # Leader sends a batch:
    # [
    #   {"id": "abc", "input": {...}},
    #   {"id": "def", "input": {...}}
    # ]
    #
    # Worker returns:
    # [
    #   {"id": "abc", "output": ..., "isError": false},
    #   {"id": "def", "output": ..., "isError": true}
    # ]
    print("here")
    return inference_batch(model, items)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=MY_PORT)
