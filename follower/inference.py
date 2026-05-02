# handles model logic; doesn't talk to the leader directly.

from typing import Any, List
import base64
import io

import torch
from PIL import Image
from torchvision import models

def load_model() -> Any:
    
    # Loads ResNet-18 once when the follower starts.
    
    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights)
    model.eval()

    preprocess = weights.transforms()
    categories = weights.meta["categories"]

    return {
        "model": model,
        "preprocess": preprocess,
        "categories": categories,
    }

def decode_base64_image(image_base64: str) -> Image.Image:
    
    # Converts base64 string into a PIL image.
    
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return image


def inference(model, input_data):
    
    # Runs ResNet-18 inference on one image input.

    #Expected input_data:{ "image_base64": "..." }
    
    if not isinstance(input_data, dict):
        raise ValueError("input_data must be a dictionary")

    if "image_base64" not in input_data:
        raise ValueError("input_data must contain 'image_base64'")

    image = decode_base64_image(input_data["image_base64"])

    resnet_model = model["model"]
    preprocess = model["preprocess"]
    categories = model["categories"]

    input_tensor = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        logits = resnet_model(input_tensor)
        #probs = torch.nn.functional.softmax(logits[0], dim=0)

    top_idx = torch.argmax(logits[0])

    return categories[top_idx.item()]


def inference_batch(model, items):
    """
    runs inference on a list of input objects

    Each item has:
    - id
    - input

    Each result returns:
    - same id
    - output
    - isError
    """

    results = []

    for item in items:
        try:
            output = inference(model, item.input)

            results.append({
                "id": item.id,
                "output": output,
                "isError": False
            })

        except Exception as e:
            # one bad input shouldn't crash whole batch
            # return an error only for that specific id
            results.append({
                "id": item.id,
                "output": str(e),
                "isError": True
            })

    return results