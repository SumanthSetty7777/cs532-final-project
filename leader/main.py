# This file is a multithreaded function that calls the api.py, heartbeat.py and queue.py, loops them and puts them together. Cancels failed tasks, etc.
from send_inference import send_inference
from add_worker import add_worker
from input_object import InputObject
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from datetime import datetime, timedelta


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
HEARTBEAT_TIMEOUT_SECONDS = 15
HEARTBEAT_CHECK_INTERVAL_SECONDS = 5

class ModelInput(BaseModel):
    data: dict #data for input

class Worker(BaseModel):
    addr: str #address of worker


@app.post("/inference")
async def inference(input: ModelInput):
    print(data["workers"])
    if(len(data["workers"]) ==0):
        return { "error": "no workers available"}
    inval = InputObject(input.data, data)
    arr = []
    async with lock:
        data["current_inputs"].append(inval)
    # Loop to control making sure that after a time minimum it is sent to the worker
    while(True):
        send = False
        # Check if batch size or time has been hit
        async with lock:
            queue_ready = len(data["current_inputs"]) >= MAX_QUEUE_SIZE
            wait_expired = data["last_sent"] + timedelta(milliseconds=MAX_QUEUE_TIME) < datetime.now()
            if len(data["current_inputs"]) > 0 and (queue_ready or wait_expired):
                arr = data["current_inputs"]
                send = True
                data["previous_inputs"].append(arr)
                data["current_inputs"] = []
                data["last_sent"] = datetime.now()
                print(f"Sending batch with {len(arr)} request(s)")
        # Send the batch to an inference machine
        if(send):
            res = await send_inference(data, arr, lock)
            c = 0
            # a bit of added fault tolerance
            while(res == -1 and c < 10):
                res = await send_inference(data, arr, lock)
                c+=1
            # Handle errors
            if res == -1:
                for val in arr:
                    async with outlock:
                        data["outputs"].append({"id": val.id, "output": "", "isError": True})
            else:
                async with outlock:
                    for result in res:
                        data["outputs"].append(result)
        async with outlock:
            for out in data["outputs"]:
                if(out["id"] == inval.id):
                    return out
        await asyncio.sleep(0.01)
                
@app.post("/heartbeat")
async def heartbeat(worker: Worker):
    async with lock:
        for w in data["workers"]:
            if w.addr == worker.addr:
                w.lastheartbeat = datetime.now()
                return {"status": "ok"}
    return {"status": "not found"}, 404

@app.post("/connect_worker")
async def connect(worker: Worker):
    async with lock:
        add_worker(data, worker)
    print("Workers: ",data["workers"])

async def monitor_worker_heartbeats():
    while True:
        await asyncio.sleep(HEARTBEAT_CHECK_INTERVAL_SECONDS)

        now = datetime.now()
        dead_workers = []

        async with lock:
            # Step 1: find workers whose heartbeat is too old
            for worker in data["workers"]:
                time_since_last_heartbeat = now - worker.lastheartbeat

                if time_since_last_heartbeat > timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS):
                    dead_workers.append(worker)

            # Step 2: for each dead worker, recover its unfinished work
            for worker in dead_workers:
                print(f"Worker timed out: {worker.addr}")

                # worker.cur_inputs is a list of batches.
                # Each batch is an array/list of InputObject objects.
                #
                # This is the "recall" part:
                # We are NOT asking the dead worker for work back.
                # We are using the leader's saved copy of what it had sent.
                for batch in worker.cur_inputs:
                    data["current_inputs"].extend(batch)

                # Step 3: remove dead worker from workers array
                data["workers"].remove(worker)

                print(f"Removed worker: {worker.addr}")
                print(f"Requeued unfinished inputs from dead worker.")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_worker_heartbeats())
