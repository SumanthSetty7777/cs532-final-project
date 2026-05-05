from utilities.unique_id import unique_id

# the object that input data maps to to give it a unique id so that outputs can be mapped to original clients
class InputObject:
    def __init__(self, input_val, data):
        self.id = unique_id(data)
        self.input = input_val

    def to_dict(self):
        return {
            "id": self.id,
            "input": self.input
        }
