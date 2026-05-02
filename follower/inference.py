# handles model logic; doesn't talk to the leader directly.

def inference(model, input_data):
    """
    Runs inference on ONE input object.
    """

    # TODO: replace this with the real model call.
    # Example:
    # output = model.predict(input_data)

    output = f"processed: {input_data}"
    return output


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