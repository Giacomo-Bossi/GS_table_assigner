class Dupe_id_error(Exception):
    def __init__(self, message="Duplicate id found."):
        self.message = message
        super().__init__(self.message)

class Undefined_id_error(Exception):
    def __init__(self, message="Undefined id found."):
        self.message = message
        super().__init__(self.message)

class Invalid_schema_error(Exception):
    def __init__(self, message="Input data does not conform to the required schema."):
        self.message = message
        super().__init__(self.message)