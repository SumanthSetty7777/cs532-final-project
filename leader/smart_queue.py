# Hung's Smart Queue that modified batch size based on latency and orders when requests go out, tracks which clients need which items.

# incoming is new inputs, erased once read, queue is the current next ones out, inworker is a list of len(num workers) with each index being that workers current inputs (map)
def smart_queue(incoming: list, queue: list, inworker: list):
    while(True):
        # handle new inputs
        x=1

        #Smart Batching
        #Dynamic Batching
        #Static Batching