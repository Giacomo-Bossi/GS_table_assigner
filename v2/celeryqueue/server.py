from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from tasks import run_mip_task
from renderer import EventInfo, generaSegnaposti

app = Flask(__name__)
CORS(app)

list_jobs = []

@app.post("/start_job")
def start_job():
    data = request.json
    # Lancia il job in background e ritorna subito l'ID
    task = run_mip_task.delay(data['tables'], data['groups'])
    list_jobs.append(task.id)
    return jsonify({"task_id": task.id}), 202

@app.get("/status/<task_id>")
def get_status(task_id):
    task = run_mip_task.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        return jsonify({"status": "COMPLETED", "result": task.result})
    elif task.state == 'PENDING':
        return jsonify({"status": "PROCESSING"}), 200
    elif task.state == 'PROGRESS':
        return jsonify({"status": "PROGRESS", "meta": task.info}), 200
    else:
        return jsonify({"status": task.state}), 200
    
@app.get("/jobs")
def list_all_jobs():
    return jsonify({"jobs": list_jobs}), 200

@app.get("/download/<task_id>/map")
def download_map(task_id):
    data = "" 
    return Response(data, mimetype='application/pdf', headers={"Content-Disposition": "attachment;filename=mappa_{}.pdf".format(task_id)})


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

if __name__ == '__main__':
    # Importante: host 0.0.0.0 per essere visibile fuori da Docker
    app.run(host='0.0.0.0', port=5000)