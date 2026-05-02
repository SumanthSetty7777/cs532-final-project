
class FollowerObject:
    def __init__(self, workeraddr, isavailable, lastheartbeat):
        # how to talk to worker, not sure exactly what this will be yet
        self.workeraddr = workeraddr
        # is the worker free (boolean)
        self.isavailable = isavailable
        # timestamp of the last heartbeat
        self.lastheartbeat = lastheartbeat


def follower_reciever(workers: list):
    while(True):
        #TODO: if worker seen, add worker to list, with free as status, append follower objects
        x=1