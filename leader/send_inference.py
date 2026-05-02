import uuid
import requests
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
    #large random id
    id = unique_id(data)
    worker = find_least_busy_worker(data)
    if(worker == -1):
        return -1
    load = [obj.to_dict() for obj in arr]

    async with lock:
        for i in range(len(data["workers"])):
            if worker.id == data["workers"][i].id:
                data["workers"][i].cur_input_count+=1
                data["workers"][i].cur_inputs.append(arr)

    headers = {}
    print(worker.addr)
    response = requests.post(worker.addr+"/inference", json=load, headers=headers)
    if not response.ok:
        return -1

    async with lock:
        for i in range(len(data["workers"])):
            if worker.id == data["workers"][i].id:
                data["workers"][i].cur_input_count-=1
                for j in range(len(data["workers"][i].cur_inputs)):
                    if(len(data["workers"][i].cur_inputs[j]) > 0):
                        if(data["workers"][i].cur_inputs[j][0].id == arr[0].id):
                            data["workers"][i].cur_inputs.pop(j)
                    else:
                        data["workers"][i].cur_inputs.pop(j)

    print(response.json())
    return response.json()