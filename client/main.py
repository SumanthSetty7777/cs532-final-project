import requests

# sends a request on an input, recieves an output
def main():
    response = requests.post("http://localhost:8000/inference", json= {"data": "a"}, headers={})
    print(response)
    #print(response.json())

if __name__ == "__main__":
    main()