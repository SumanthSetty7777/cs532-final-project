from utilities.unique_id import unique_id
from datetime import datetime

# The object to store the idea of a worker and all its data needed for communication and load balancing
class Worker:
    def __init__(self, id, ip):
        self.cur_input_count = 0
        self.cur_inputs = []
        self.id = id
        self.addr = ip
        self.lastheartbeat = datetime.now()

# the function needed to add workers to a list in data so that newly connected workers can be communicated with
def add_worker(data, worker):
    id = unique_id(data)
    machine = Worker(id, worker.addr)
    data["workers"].append(machine)
    print("Workers: ", data["workers"])
    return 0
