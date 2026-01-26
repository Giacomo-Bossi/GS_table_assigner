from celery import Celery
from celery.utils.log import get_task_logger
import mip
import time
import Table_problem_optimizer as Opt

# NOTA: host='redis', non 'localhost'
celery_app = Celery('tasks', 
                    broker='redis://redis:6379/0', 
                    backend='redis://redis:6379/0')

# Celery task-aware logger
logger = get_task_logger(__name__)

# --- DEFINIZIONE Estimated Incumbent UPDATER ---
class CeleryUpdater():
    def __init__(self, model, task_instance, group_sizes):
        self.model = model
        self.task_instance = task_instance
        self.last_update_time = time.time()
        self.group_sizes = group_sizes
        self.max = 0

    def generate_constrs(self, osi_model, depth, npass):
        # Calcola persone assegnate dalla soluzione parziale
        if time.time() - self.last_update_time > 1:
            somma = 0
            for i in range(len(osi_model.vars)):
                if osi_model.vars[i].name.startswith("assign"):
                    if osi_model.vars[i].x >= 0.99:
                        somma += self.group_sizes[int(osi_model.vars[i].name.split("_g")[1].split("_t")[0])]
                
            if(self.max < somma):
                self.max = somma
                # Invia aggiornamento di progresso al task Celery
                self.task_instance.update_state(state='PROGRESS', meta={'current': self.max + self.task_instance.incumbent_offset, 'total': sum(self.group_sizes) + self.task_instance.incumbent_offset})
                logger.info(f"##### Progresso: {self.max} boh.")

            
            self.last_update_time = time.time()
        return
    
@celery_app.task(bind=True)
def run_mip_task(self, data:dict):
    self.unhandled_groups = data.get("assignments_groups", [])
    self.unhandled_assignments = data.get("assignments", {})
    self.incumbent_offset = sum(group["size"] for group in self.unhandled_groups)

    optim = Opt.Table_problem_optimizer(data,minimize_entropy=False)
    optim.model.cuts_generator = CeleryUpdater(optim.model, self, [g["size"] for g in data["groups"]])
    optim.solve_problem()
    json = optim.get_solution_json()
    json["groups"].extend(self.unhandled_groups)
    for table_id, assigned_groups in self.unhandled_assignments.items():
        if table_id not in json["pairings"]:
            json["pairings"][table_id] = []
            json["used_tables"]+= 1
        json["pairings"][table_id][:0] = assigned_groups
    json["total assignable"]+= self.incumbent_offset
    json["total seats"]+= self.incumbent_offset
    json["total guests"]+= self.incumbent_offset


    return json
