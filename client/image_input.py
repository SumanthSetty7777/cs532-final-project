import base64
import requests

def image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

image_base64 = image_to_base64("./dog.jpeg")

payload = {
    "data": {
        "image_base64": image_base64
    }
}

response = requests.post(
    "http://localhost:8000/inference",
    json=payload
)

print("Status:", response.status_code)
print("Text:", response.text)

try:
    print("JSON:", response.json())
except Exception as e:
    print("Could not parse JSON:", e)
