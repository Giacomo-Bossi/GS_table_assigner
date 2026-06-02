from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from tasks import run_mip_task
from renderer import EventInfo, generaSegnaposti, generaMappa
import os
from redis import Redis
import json


redis_client = Redis(host="redis", port=6379, db=0, decode_responses=True)

app = Flask(__name__)
CORS(app)

list_jobs = []

@app.post("/start_job")
def start_job():
    data = request.json
    # Lancia il job in background e ritorna subito l'ID
    task = run_mip_task.delay(data)
    list_jobs.append(task.id)
    return jsonify({"task_id": task.id}), 202

@app.get("/status/<task_id>")
def get_status(task_id):
    task = run_mip_task.AsyncResult(task_id) 
    print(f"Task {task_id} state: {task.state}")
    
    # Safely get date_done as a string, since datetime objects can't be JSON serialized by default
    date_done_str = task.date_done.isoformat() if task.date_done else None

    if task.state == 'SUCCESS':
        return jsonify({"status": "COMPLETED", "result": task.result, "date": date_done_str})
    elif task.state == 'PENDING':
        return jsonify({"status": "PROCESSING", "date": date_done_str}), 200
    elif task.state == 'PROGRESS':
        return jsonify({"status": "PROGRESS", "meta": task.info, "date": date_done_str}), 200
    else:
        return jsonify({"status": task.state, "date": date_done_str}), 200
    

@app.get("/jobs")
def list_all_jobs():
    r = redis_client
    try:
        keys = r.keys("celery-task-meta-*")
        tasks_info = []
        for k in keys:
            tid = k.split("celery-task-meta-", 1)[1]
            try:
                val = r.get(k)
                data = json.loads(val)
                # date_done is usually an ISO-8601 string in the meta dictionary
                date_done_str = data.get('date_done') or ""
                tasks_info.append((tid, date_done_str))
            except Exception:
                tasks_info.append((tid, ""))
        
        # Sort in reverse order based on date_done string
        tasks_info.sort(key=lambda x: x[1], reverse=True)
        sorted_task_ids = [t[0] for t in tasks_info]
        
        return jsonify({"jobs": sorted_task_ids, "keys": keys}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/download/<task_id>/map")
def download_map(task_id):
    task = run_mip_task.AsyncResult(task_id)
    if task.state != 'SUCCESS':
        return jsonify({"error": "Task not completed"}), 400
    
    try:
        data = generaMappa(task.result, title="FESTA D'INVERNO 2026")
        return Response(data, mimetype='application/pdf' )# , headers={"Content-Disposition": "attachment;filename=mappa_{}.pdf".format(task_id)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/download/<task_id>/placeholders")
def download_placeholders(task_id):
    event = EventInfo("Festa", "d'inverno", "2026", "Sabato 31 Gennaio 2026")
    task = run_mip_task.AsyncResult(task_id)
    if task.state != 'SUCCESS':
        return jsonify({"error": "Task not completed"}), 400
    gruppi = task.result.get("groups", [])
    prenotazioni = [(g.get("show_name", "Ospite " + str(i)), g.get("size", 1)) for i, g in enumerate(gruppi)]

    data = generaSegnaposti(prenotazioni, event)
    return Response(data, mimetype='application/pdf', headers={"Content-Disposition": "attachment;filename=segnaposti_{}.pdf".format(task_id)})

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)