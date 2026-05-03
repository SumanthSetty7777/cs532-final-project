import uuid
import httpx # type: ignore
from utilities.unique_id import unique_id
import asyncio

def find_least_busy_worker(data):
    if(len(data["workers"])==0):
        return -1
    
    min_inputs = data["workers"][0].cur_input_count
    min_worker = data["workers"][0]
    for worker in data["workers"]:
        if(worker.cur_input_count < min_inputs):
            min_worker = worker
            min_inputs = worker.cur_input_count
    return min_worker

async def send_inference(data, arr, lock):
    worker = find_least_busy_worker(data)
    if worker == -1:
        return -1

    load = [obj.to_dict() for obj in arr]

    async with lock:
        for i in range(len(data["workers"])):
            if worker.id == data["workers"][i].id:
                data["workers"][i].cur_input_count += 1
                data["workers"][i].cur_inputs.append(arr)

    print("Sending to worker:", worker.addr)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(worker.addr + "/inference", json=load)

        print("Worker status:", response.status_code)
        print("Worker text:", response.text)

        if response.status_code != 200:
            return -1

        result_json = response.json()

    except Exception as e:
        print("Error calling worker:", e)
        return -1

    async with lock:
        for i in range(len(data["workers"])):
            if worker.id == data["workers"][i].id:
                data["workers"][i].cur_input_count -= 1
                data["workers"][i].cur_inputs = [
                    batch for batch in data["workers"][i].cur_inputs
                    if not (len(batch) > 0 and batch[0].id == arr[0].id)
                ]

    return result_json