from flask import Flask, request, jsonify
from tasks import run_mip_task

app = Flask(__name__)

@app.post("/start_job")
def start_job():
    data = request.json
    # Lancia il job in background e ritorna subito l'ID
    task = run_mip_task.delay(data['tables'], data['groups'])
    return jsonify({"task_id": task.id}), 202

@app.get("/status/<task_id>")
def get_status(task_id):
    task = run_mip_task.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        return jsonify({"status": "COMPLETED", "result": task.result})
    elif task.state == 'PENDING':
        return jsonify({"status": "PROCESSING"}), 200
    else:
        return jsonify({"status": task.state}), 200
    
if __name__ == '__main__':
    # Importante: host 0.0.0.0 per essere visibile fuori da Docker
    app.run(host='0.0.0.0', port=5000)