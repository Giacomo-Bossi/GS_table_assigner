from Optimizer.data_parser import ILP_data_parser
from Optimizer.error_types import *
import jsonschema
from typing import Callable
from Optimizer.solver_utils import Table, Reservation
from Optimizer.presolution_steps import sanitize_tables

class Solver_handler():
    def __init__(self,data):
        #warnings are non critical issues with the data that should be reported to the user 
        #but do not prevent the solver from running, such as duplicate table names or reservation names.
        self.data = data
        self.warnings = []  

        try:
            self.parser = ILP_data_parser(self.data)
        except Invalid_schema_error as e:
            raise e
        except Invalid_data_error as e:
            raise e

        self.tables = self.parser.parse_tables()
        self.reservations = self.parser.parse_reservations()
        self.current_tables = self.tables.copy()
        self.current_reservations = self.reservations.copy()
        self.assigned_res_names = set() 
        self.assignments = {} #dict of table_id to list of reservation names, used to keep track of assignements thorugh steps
        self.assignments = {t.get_table_id(): [] for t in self.tables}
        self.final_reservations = []

        self.total_seats = sum(t.get_capacity() for t in self.tables)

        self.presolution_steps = []
                    
    def configure_presolver(self,presolution_steps:list[Callable]):
        """
        Configures the solver with the parsed tables and reservations, and any additional constraints or parameters.
        """
        self.presolution_steps = presolution_steps


    def run_solution_steps(self):
        """Runs the solution steps in sequence. Updates itself in between steps.
        """        
        for step in self.presolution_steps:
            print(f"Running step: {step.__name__}")
            step(self.current_tables, self.current_reservations, self.warnings,self.assignments,self.final_reservations)
            self.current_tables = sanitize_tables(self.current_tables)

            
    def get_results(self):
        """Returns the final results after running the solution steps.
        """
        used_tab = sum(1 for assign in self.assignments.values() if len(assign) > 0)
        
        total_guests = sum(r.get_real_size() for r in self.reservations)
        total_assignable = sum(
            r["real_size"]
            for r in self.final_reservations
            if r["name"] in [name for names in self.assignments.values() for name in names]
        )

        return {
            "pairings": self.assignments,
            "used_tables": used_tab,
            "total seats": self.total_seats,
            "total guests": total_guests,
            "total assignable": total_assignable,
            "warnings": self.warnings,
            "groups": self.final_reservations
        } 