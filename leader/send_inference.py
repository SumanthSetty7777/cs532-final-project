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

def send_inference(data, arr, lock):
    #large random id
    id = unique_id(id)
    worker = find_least_busy_worker(data)
    if(worker == -1):
        return -1
    data = {"inputs": arr}

    headers = {}
    response = requests.post(worker.ip+"/inference", data=data, headers=headers)


    return response