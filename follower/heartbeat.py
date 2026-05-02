# heartbeat.py
# Follower-side helper file.
# This lets the follower talk back to the leader.

import time
import requests


def connect_to_leader(leader_url, my_addr):
    # runs once when the follower starts --> tells leader to add me as a worker; my addr is my_addr.

    try:
        response = requests.post(
            f"{leader_url}/connect_worker",
            json={"addr": my_addr}
        )

        print(f"Connected to leader: {response.status_code}")
        return response

    except requests.exceptions.RequestException as e:
        print(f"Could not connect to leader: {e}")
        return None


def heartbeat_loop(leader_url, my_addr, interval_seconds=5):
    # runs forever in the background --> tells the leader I'm still alive.

    while True:
        try:
            response = requests.post(
                f"{leader_url}/heartbeat",
                json={"addr": my_addr}
            )

            print(f"Heartbeat sent: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Could not send heartbeat: {e}")

        time.sleep(interval_seconds)