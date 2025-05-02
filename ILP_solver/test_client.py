import requests
from utils import JSON_generate_input
url = "http://localhost:8081"

data = JSON_generate_input([24,5,48],[4,23])

try:
    response = requests.post(url,json=data)
    print("response status :",response.status_code)
    print("contnet :", response.text)
except requests.exceptions.RequestException as e:
    print("Error : ",e)