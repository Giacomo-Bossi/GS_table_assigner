from celery import Celery
from celery.utils.log import get_task_logger
import mip
import time

# NOTA: host='redis', non 'localhost'
celery_app = Celery('tasks', 
                    broker='redis://redis:6379/0', 
                    backend='redis://redis:6379/0')

# Celery task-aware logger
logger = get_task_logger(__name__)

# --- DEFINIZIONE INCUMBENT UPDATER ---
class CeleryUpdater(mip.IncumbentUpdater):
    def __init__(self, model, task_instance, T, G, group_sizes):
        super().__init__(model)
        self.model = model
        self.task_instance = task_instance
        self.last_update_time = time.time()
        self.T = T
        self.G = G
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
                self.task_instance.update_state(state='PROGRESS', meta={'current': self.max, 'total': sum(self.group_sizes)})
                logger.info(f"##### Progresso: {self.max} boh.")

            
            self.last_update_time = time.time()
        return
    
    

def calculate_table_penalty(num_tables : int)->float:
    """
    assign the table penalty in a way that does not affect the number of people that can fit
    """
    return 1/(num_tables+1)

@celery_app.task(bind=True)
def run_mip_task(self, tables: dict, guests: dict) -> dict:


    # Compact index mapping
    T = list(range(len(tables)))
    G = list(range(len(guests)))

    tables_cap = [t["capacity"] for t in tables]
    group_sizes = [g["size"] for g in guests]

    num_tables = len(T)
    table_penalty = calculate_table_penalty(num_tables)

    model = mip.Model(sense=mip.MAXIMIZE)
    model.store_search_progress_log = True
    #model.incumbent_updater = CeleryUpdater(model, self)
    
    
    logger.info("Starting optimization...")

    # Variables
    assign = [[model.add_var(var_type=mip.BINARY, name=f"assign_g{str(i)}_t{str(j)}")
               for j in T] for i in G]

    used = [model.add_var(var_type=mip.BINARY) for j in T]

    # Capacity constraints
    for j in T:
        model.add_constr(
            mip.xsum(assign[i][j] * group_sizes[i] for i in G)
            <= tables_cap[j]
        )

    # Linking (faster version)
    for j in T:
        model.add_constr(
            mip.xsum(assign[i][j] for i in G) >= used[j]
        )

    # Each group at most once
    for i in G:
        model.add_constr(
            mip.xsum(assign[i][j] for j in T) <= 1
        )

    # Objective
    model.objective = (
        mip.xsum(assign[i][j] * group_sizes[i] for i in G for j in T)
        - table_penalty * mip.xsum(used[j] for j in T)
    )
    model.cuts_generator = CeleryUpdater(model, self, T, G, group_sizes)
    model.optimize(relax=False, max_seconds=30)


    # Output
    if not model.num_solutions:
        return {"error": "no solution"}

    table_assignments = {j: [] for j in T}
    for i in G:
        for j in T:
            if assign[i][j].x >= 0.99:
                table_assignments[j].append(i)

    return {
        "pairings": table_assignments,
        "used_tables": int(sum(used[j].x for j in T)),
        "total seats": sum(tables_cap),
        "total guests": sum(group_sizes),
        "total assignable": sum(
            group_sizes[i] for i in G
            if any(assign[i][j].x >= 0.99 for j in T)
        )
    }