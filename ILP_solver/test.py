import jsonschema
import json

with open("input_schema.json", "r") as schema_file:
    schema = json.load(schema_file)
with open("input.json", "r") as data_file:
    data = json.load(data_file)
try:
    jsonschema.validate(instance=data, schema=schema)
    print("JSON is valid")
except jsonschema.exceptions.ValidationError as e:
    print("JSON is invalid")
    print(e)

