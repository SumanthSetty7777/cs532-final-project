# This file is a multithreaded function that calls the api.py, heartbeat.py and queue.py, loops them and puts them together. Cancels failed tasks, etc.
from send_inference import send_inference
from add_worker import add_worker
from input_object import InputObject
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
        "workers":[], #array of worker id, worker ip, busy score/number of active inputs being worked on
        "outputs": []
        }
lock = asyncio.Lock()
outlock = asyncio.Lock()

# Constants
MAX_QUEUE_SIZE = 5
MAX_QUEUE_TIME = 1000

class ModelInput(BaseModel):
    data: str #data for input

class Worker(BaseModel):
    addr: str #address of worker


@app.post("/inference")
async def inference(input: ModelInput):
    if(len(data["workers"] ==0)):
        return {"error": "no workers available"}
    inval = InputObject(input.data)
    async with lock:
        data["current_inputs"].append(inval)
    async with lock:
        if len(data["current_inputs"]) > MAX_QUEUE_SIZE or data["last_sent"]-MAX_QUEUE_TIME > datetime.now():
            arr = data["current_inputs"]
            send = True
            # TODO might an an id here not sure probably should idk
            data["previous_inputs"].append(arr)
            data["current_inputs"] = []

    if(send):
        res = send_inference(data, lock)
        c = 0
        while(res == -1 and c < 10):
            res = send_inference(data, lock)
        if res == -1:
            for val in arr:
                async with outlock:
                    data["outputs"].append({"id": val.id, "output": "", "error": True})
        else:
            for result in res:
                data["outputs"].append(result)
    while(True):
        for out in data["outputs"]:
            if(out.id == inval.id):
                return inval
@app.post("/connect_worker")
async def connect(worker: Worker):
    async with lock:
        add_worker(data, worker)
    
        