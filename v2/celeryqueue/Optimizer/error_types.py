class Invalid_data_error(Exception):
    def __init__(self, message="Input data is ambiguous or contains invalid references."):
        self.message = message
        super().__init__(self.message)

class Invalid_schema_error(Exception):
    def __init__(self, message="Input data does not conform to the required schema."):
        self.message = message
        super().__init__(self.message)