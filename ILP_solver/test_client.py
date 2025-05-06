import requests
from utils import JSON_generate_input
from jsonschema import validate
from jsonschema.exceptions import ValidationError

import json
url = "http://localhost:8081"

data = JSON_generate_input([24,5,4],[4,23])

with open("schemas/input_schema.json", "r") as schema_file:  
        schema = json.load(schema_file)

try:
    validate(schema, data)
    print("input was validated")
    response = requests.post(url,json=data)
    print("response status :",response.status_code)
    print("content :", response.text)
except requests.exceptions.RequestException as e:
    print("Error : ",e)
except ValidationError as e:
     print("input is invalid")