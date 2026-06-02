from celery import Celery
from celery.utils.log import get_task_logger
import mip
import time
from Optimizer.presolution_steps import *
from Optimizer.Solver_handler import Solver_handler

# NOTA: host='redis' punta al docker "redis"
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

    solver_handler = Solver_handler(data)
    solver_handler.configure_presolver([preassign_close_to_field, split_massive_reservations, test_all_even, run_solver_final])
    solver_handler.run_solution_steps()
    json = solver_handler.get_results()

    #optim.model.cuts_generator = CeleryUpdater(optim.model, self, [g["size"] for g in data["groups"]]) ## solver implementation changed, deprecated old method
    return json
