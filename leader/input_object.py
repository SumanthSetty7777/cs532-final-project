from utilities.unique_id import unique_id

class InputObject:
    def __init__(self, input_val):
        self.id = unique_id()
        self.input = input_val