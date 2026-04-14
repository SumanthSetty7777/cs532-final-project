# Checks which workers are online with periodic heartbeats

def heartbeats(workers: list):
    while(True):
        #sends a heartbeat to each worker
        x=1