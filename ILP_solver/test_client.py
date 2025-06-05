import requests
from utils import JSON_generate_input
from jsonschema import validate
from jsonschema.exceptions import ValidationError

import json
url = "http://localhost:8081"

data = JSON_generate_input([10,3,8,10,12,7],[10,6,5,8,4,9,5])

with open("schemas/input_schema.json", "r") as schema_file:  
        schema = json.load(schema_file)
with open("schemas/output_schema.json",'r') as schema_file:
        schema2 = json.load(schema_file)
try:
    validate(schema, data)
    print("input was validated")
    response = requests.post(url,json=data)
    print("response status :",response.status_code)
    print("content :", response.text)
    validate(schema2, json.loads(response.text))
except requests.exceptions.RequestException as e:
    print("Error : ",e)
except ValidationError as e:
     print("input is invalid")