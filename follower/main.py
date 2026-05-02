# The central loop that recieves requests, runs an inference, returns outputs
from inference import inference
from heartbeat import heartbeat
import requests

def main():
    model = 1 # load model
    # main loop of a follower/inference machine
    #Thread 1: run heartbeat
    heartbeat()

    #Thread 2: main loop/inference
        # Take input from leader
        # Inference on Input
        # Send inference back to leader
        # Wait for new input from leader
    while True:
        #waiting for input
        input = 0 # fix
        inference(model,input)
        #send output to server
    