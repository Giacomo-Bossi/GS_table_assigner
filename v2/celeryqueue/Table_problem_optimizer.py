import json
import mip
import time
from mip import OptimizationStatus

def calculate_lambda_coeff(num_tables : int)->float:
        """
        assigns the table penalty in a way that does not affect the number of people that can fit
        """
        return 1/(num_tables+1)

class Prog_id_gen():
    def __init__(self):
        self.curr_id = 0
    def get_next(self):
        ret = self.curr_id
        self.curr_id+=1
        return ret

class Table():
    def __init__(self,table,prog_id):
        self.table_id = table["table_id"]
        self.capacity = table["capacity"]
        self.head_seats = table.get("head_seats", 0)
        self.model_id = prog_id

class Reservation():          
    def __init__(self,reservation,prog_id):
          self.name = reservation["name"]
          self.size = reservation["size"]
          self.require_head = reservation.get("required_head",0)
          self.model_id = prog_id
        
class Table_problem_optimizer():
    def __init__(self,json_object,minimize_entropy=False):
        
        self.tables = []
        id_gen = Prog_id_gen()

        for table in json_object["tables"]:
            self.tables.append(Table(table,id_gen.get_next()))

        self.reservations = []
        id_gen = Prog_id_gen()

        for res in json_object["groups"]:
            self.reservations.append(Reservation(res,id_gen.get_next()))

        self.grps = json_object["groups"]
        self.model = mip.Model(sense=mip.MAXIMIZE)

        #self.model.max_mip_gap = 0.02 #2% tolerance to best possible solution
        self.model.max_seconds = 30
        self.minimize_entropy = minimize_entropy
        self.solution_available = False

    def solve_problem(self):
        self.add_contraints()
        self.add_utility_function()
        self.model_summary()

        start_time = time.time()

        status = self.model.optimize()

        if status in [OptimizationStatus.ERROR,OptimizationStatus.INFEASIBLE,OptimizationStatus.INT_INFEASIBLE,OptimizationStatus.UNBOUNDED]:
            return
        
        elapsed_time = time.time() - start_time

        print(f"Optimization time: {elapsed_time:.2f} seconds")
        print(f"Optimization status: {self.model.status}")
        print(f"Optimal value: {self.model.objective_value}")
        self.solution_available = True

    def add_contraints(self):

        self.assignement_vars = [[self.model.add_var(var_type=mip.BINARY,name=f"assign_g{str(i.model_id)}_t{str(j.model_id)}")
                                   for j in self.tables] for i in self.reservations]
        
        #table capacity constraints  
        for tab in self.tables:
            self.model.add_constr(
                mip.xsum(self.assignement_vars[res.model_id][tab.model_id] * res.size for res in self.reservations) <= tab.capacity
            )

        # Each group at most one table
        for res in self.reservations:
            self.model.add_constr(
                mip.xsum(self.assignement_vars[res.model_id][tab.model_id] for tab in self.tables) <= 1
            )

        head_reservations = [res for res in self.reservations if res.require_head == True]

        #head reservation constraints
        for tab in self.tables:
            self.model.add_constr(
                mip.xsum(self.assignement_vars[res.model_id][tab.model_id] for res in head_reservations ) <= tab.head_seats
            )
        
        if self.minimize_entropy:

            self.full_tables = [self.model.add_var(var_type=mip.BINARY) for i in self.tables]   
            #full tables linking
            for tab in self.tables:
                self.model.add_constr(self.full_tables[tab.model_id] <=
                                    1 - (tab.capacity - mip.xsum(self.assignement_vars[res.model_id][tab.model_id] * res.size for res in self.reservations))/tab.capacity)
                

    def add_utility_function(self):

        if self.minimize_entropy:
            λ = calculate_lambda_coeff(len(self.tables))
            self.model.objective = (
                    mip.xsum(self.assignement_vars[res.model_id][tab.model_id] * res.size 
                            for res in self.reservations 
                            for tab in self.tables) +
                            λ * mip.xsum(self.full_tables[tab.model_id] for tab in self.tables)
            )
                
        else:
            self.model.objective = (
                    mip.xsum(self.assignement_vars[res.model_id][tab.model_id] * res.size 
                            for res in self.reservations 
                            for tab in self.tables) 
            )  

    def model_summary(self):
            print(f"Number of variables: {self.model.num_cols}")
            print(f"Number of constraints: {self.model.num_rows}")
            print(f"Number of tables: {len(self.tables)}")
            print(f"Number of reservations: {len(self.reservations)}")
            print(f"Total capacity: {sum(t.capacity for t in self.tables)}")
            print(f"Total guests: {sum(r.size for r in self.reservations)}")
            print(f"Minimize tables: {self.minimize_entropy}")
    
    def write_sol_to_file(self,path="out.json")->None:
        sol = self.get_solution_json()
        with open(path,"w") as f:
            json.dump(sol,f,indent=1)

    #def set_cuts_generator(generator):
    #   self.model.

    def get_solution_json(self)->dict:
        if not self.solution_available:
            return {"error": "no solution"}
        else:
            pairings = {str(tab.table_id) : [] for tab in self.tables}
            tot_seats = sum(table.capacity for table in self.tables)
            tot_guests = sum(res.size for res in self.reservations)
            assigned_res = [res for res in self.reservations if any(self.assignement_vars[res.model_id][tab.model_id].x == 1.0 for tab in self.tables)]
            tot_assigned = sum(res.size for res in assigned_res)

            for tab in self.tables:
                for res in self.reservations:
                    if self.assignement_vars[res.model_id][tab.model_id].x == 1.0:
                        pairings[str(tab.table_id)].append(str(res.name))

            used_tab = sum(1 for pair in pairings.values() if len(pair) > 0)

            return {
            "pairings": pairings,
            "used_tables": used_tab, 
            "total seats": tot_seats,
            "total guests": tot_guests,
            "total assignable": tot_assigned,
            "groups": self.grps
            }
    
if __name__ == "__main__":
    with open("C:\\Users\\giaco\\projects\\python\\tmp\\GS_table_assigner\\ILP_solver\\Examples\\csvconvert-impossible.json","r") as file:
        opt = Table_problem_optimizer(json.load(file))
        opt.solve_problem()
        opt.write_sol_to_file("out.json")