from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from utils import process_request

schema = None

class table_assign_RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global schema
        try:
            if self.headers['Content-Type'] != 'application/json':
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Content-Type must be application/json"}).encode('utf-8'))
                return
            
            lenght = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(lenght))

            validate(schema, data)
            print("input was validated")
            sol = process_request(data)
            #sol = solve_instance(data)
            sol = 4
            sol=json.dumps(sol)
            self.send_response(200)
            self.send_header('Content_type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(sol,"utf8"))

        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Error when decoding the json"}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        except ValidationError as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "JSON does not match the schema", "details": str(e)}).encode('utf-8'))


def run(IP_address,port):
    global schema
    print(f"starting the server at : {IP_address}:{port}...")
    with open("schemas/input_schema.json", "r") as schema_file:  
        schema = json.load(schema_file)
    server_address=(IP_address,port)
    server = HTTPServer(server_address,table_assign_RequestHandler)
    print("server has started")
    server.serve_forever()

run("127.0.0.1", 8081)