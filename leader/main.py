# This file is a multithreaded function that calls the api.py, heartbeat.py and queue.py, loops them and puts them together. Cancels failed tasks, etc.
from follower_reciever import follower_reciever
from heartbeat import heartbeats
from smart_queue import smart_queue
from api import api

def main():
    # Stores data about each worker
    workers = []
    # Stores the stuff that comes into the api until its queued
    incoming = []
    # Queues up the stuff to do
    queue = []
    # Stores what info is in the workers
    inworker = []

    # (Thread 1): run worker connector
    follower_reciever(workers= workers)

    # (Thread 2): run the heartbeat
    heartbeats(workers=workers)

    # (Thread 3): start queue
    smart_queue(incoming=incoming,  queue = queue, inworker = inworker)

    # (Thread 4): api
    api(incoming=incoming)