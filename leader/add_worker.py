from utilities.unique_id import unique_id

class Worker:
    def __init__(self, id, ip):
        self.cur_input_count = 0
        self.cur_inputs = []
        self.id = id
        self.addr = ip

def add_worker(data, worker):
    id = unique_id()
    machine = Worker(id, worker.addr)
    data["workers"].append(machine)
    return 0