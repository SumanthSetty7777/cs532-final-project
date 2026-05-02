# This file is a multithreaded function that calls the api.py, heartbeat.py and queue.py, loops them and puts them together. Cancels failed tasks, etc.
from send_inference import send_inference
from add_worker import add_worker
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from datetime import datetime


app = FastAPI()
#current inputs is data waiting to be sent to a workers, previous inputs is a 2D array of data in workers
data = {"current_inputs": [], 
        "previous_inputs": [], 
        "last_sent": datetime.now(), 
        "ids": [], 
        "workers":[] #array of worker id, worker ip, busy score/number of active inputs being worked on
        }
lock = asyncio.Lock()

# Constants
MAX_QUEUE_SIZE = 5
MAX_QUEUE_TIME = 1000

class ModelInput(BaseModel):
    data: str #data for input

class Worker(BaseModel):
    addr: str #address of worker


@app.post("/inference")
async def inference(input: ModelInput):
    async with lock:
        data["current_inputs"].append(input)
        if len(data["current_inputs"]) > MAX_QUEUE_SIZE or data["last_sent"]-MAX_QUEUE_TIME > datetime.now():
            send_inference(data)


@app.post("/connect_worker")
async def connect(worker: Worker):
    async with lock:
        add_worker(data, worker)

