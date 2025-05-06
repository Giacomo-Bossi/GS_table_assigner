from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from model import solve_instance
from utils import input_id_checker

class table_assign_RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if self.headers['Content-Type'] != 'application/json':
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Content-Type must be application/json"}).encode('utf-8'))
                return
            
            lenght = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(lenght))
            if not data.get('tables') or not data.get('groups'):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Tables or groups data cannot be empty"}).encode('utf-8'))
                return

            if not input_id_checker(data['tables'],data['groups']):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid format on the ids"}).encode('utf-8'))
                return

            
                
            print("Solving the probelm...")
            sol = solve_instance(data)
            print("problem solved!")
            sol=json.dumps(sol)
            self.send_response(200)
            self.send_header('Content_type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(sol,"utf8"))
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON format"}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

def run(IP_address,port):
    print(f"starting the server at : {IP_address}:{port}...")
    server_address=(IP_address,port)
    server = HTTPServer(server_address,table_assign_RequestHandler)
    print("server has started")
    server.serve_forever()

run("127.0.0.1", 8081)