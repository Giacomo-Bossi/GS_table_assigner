from data_parser import ILP_data_parser
from error_types import *
import jsonschema
from typing import Callable

class Solver_handler():
    def __init__(self,data):
        #warnings are non critical issues with the data that should be reported to the user 
        #but do not prevent the solver from running, such as duplicate table names or reservation names.
        self.data = data
        self.warnings = []  

        try:
            self.parser = ILP_data_parser(self.data)
        except Invalid_schema_error as e:
            pass #TODO handle
        except Invalid_data_error as e:
            pass 

        self.tables = self.parser.parse_tables()
        self.reservations = self.parser.parse_reservations()
        self.current_tables = self.tables.copy()
        self.current_reservations = self.reservations.copy()
        self.assigned_res_names = set() 
        self.assignments = {} #dict of table_id to list of reservation names, used to keep track of assignements thorugh steps
        self.assignments = {t.get_table_id(): [] for t in self.tables}

        self.presolution_steps = []
    

    def update_current_state(self,new_assignments:dict[str,list[str]]):
        """Updates the current tables, reservations and assignements based on new assignements from a presolver step.
        """
        #update assignements with new assignements
        self.current_tables = []
        self.current_reservations = []

        #update reservations
        for table_id, res_names_list in new_assignments.items():
            for res_name in res_names_list:
                self.assigned_res_names.add(res_name)
                self.assignments[table_id].append(res_name)
                
        self.current_reservations = [
            r for r in self.reservations
            if r.get_name() not in self.assigned_res_names
        ]

        #update tables
        for tab in self.tables:
            if len(self.assignments[tab.get_table_id()]) > 0:
                resized_table = tab.copy()

                assigned_size = sum(
                    r.get_size() for r in self.reservations
                    if r.get_name() in self.assignments[tab.get_table_id()]
                )
               
                remaining_capacity = tab.get_capacity() - assigned_size
                if remaining_capacity < 0: 
                    raise ValueError(f"Table {tab.get_table_id()} overassigned: assigned size {assigned_size} \
                                     exceeds capacity {tab.get_capacity()}.")
                
                resized_table.resize(remaining_capacity)

                heads_assigned = sum(
                    r.get_require_head() for r in self.reservations
                    if r.get_name() in self.assignments[tab.get_table_id()]
                )
                remaining_head_seats = tab.get_head_seats() - heads_assigned
                if remaining_head_seats < 0:
                    raise ValueError(f"Table {tab.get_table_id()} overassigned head seats: assigned head seats \
                                     {heads_assigned} exceeds head seat capacity {tab.get_head_seats()}.")
                resized_table.set_head_seat(remaining_head_seats)

                self.current_tables.append(resized_table)
            else:
                self.current_tables.append(tab)
                
    def configure_presolver(self,presolution_steps:list[Callable]):
        """
        Configures the solver with the parsed tables and reservations, and any additional constraints or parameters.
        """
        self.presolution_steps = presolution_steps

    def run_solution_steps(self):
        """Runs the solution steps in sequence. Updates itself in between steps.
        """        
        for step in self.presolution_steps:
            new_assignements = step(self.current_tables, self.current_reservations, self.warnings)

            self.update_current_state(new_assignements)

    def get_results(self):
        """Returns the final results after running the solution steps.
        """
        used_tab = sum(1 for assign in self.assignments.values() if len(assign) > 0)
        total_seats = sum(t.get_capacity() for t in self.tables)
        total_guests = sum(r.get_size() for r in self.reservations)
        total_assignable = sum(
            r.get_size()
            for r in self.reservations
            if r.get_name() in self.assigned_res_names
        )

        return {
            "pairings": self.assignments,
            "used_tables": used_tab,
            "total seats": total_seats,
            "total guests": total_guests,
            "total assignable": total_assignable,
            "warnings": self.warnings
        } 