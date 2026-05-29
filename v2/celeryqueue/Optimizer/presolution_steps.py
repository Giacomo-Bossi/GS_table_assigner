from solver_utils import Table, Reservation
from Table_problem_optimizer import Table_problem_optimizer, calculate_lambda_coeff

NEAR_FIELD_ATTR = "near_field"

def preassign_close_to_field(table_list:list[Table], reservation_list:list[Reservation], warnings_list:list[str]):
    """
    presolver step that preassigns reservations with "close_to_field" requirement to tables with "close_to_field" attribute.
    """ 
    groups_to_preassign = [res for res in reservation_list if res.get_near_field()]
    field_tables = [table for table in table_list if table.get_near_field()]

    if len(field_tables) == 0 and len(groups_to_preassign) > 0:
        warnings_list.append(f"{len(groups_to_preassign)} reservations require {NEAR_FIELD_ATTR} but no tables have this attribute. Ignoring it")
        return
    

    if sum(1 for res in groups_to_preassign if res.get_require_head()) > \
        sum(1 for tab in field_tables if tab.get_head_seats() > 0):

        warnings_list.append(f"{len(groups_to_preassign)} reservations require {NEAR_FIELD_ATTR} and head seats,\
                              but not enough tables with {NEAR_FIELD_ATTR} have head seats.\
                              Ignoring {NEAR_FIELD_ATTR} requirement for these reservations.")
        
        for res in groups_to_preassign:
            if res.get_near_field():
                res.set_near_field(False)
                groups_to_preassign.remove(res)

    
    Optimizer = Table_problem_optimizer(field_tables, groups_to_preassign, minimize_entropy=True)
    Optimizer.solve_problem()

    if not Optimizer.solution_available:
        warnings_list.append(f"Failed to find a solution during presolver step {preassign_close_to_field.__name__}, skipping preassignment.")
        return
    
    solution = Optimizer.get_solution_json()
    new_assignements = solution.get("pairings",{})
    return new_assignements

def split_large_reservations(table_list:list[Table], reservation_list:list[Reservation], warnings_list:list[str]):
    """
    presolver step that splits reservations that are larger than any table capacity into smaller reservations.
    """ 
    max_capacity = max(table.get_capacity() for table in table_list)
    big_groups = [res for res in reservation_list if res.get_size() > max_capacity]
    new_assignments = {}
    while len(big_groups)>0:
        pass

def run_solver_final(tables:list[Table], reservations:list[Reservation], warnings_list:list[str]):
    """
    runs the solver with the remaining tables and reservations.
    """ 
    Optimizer = Table_problem_optimizer(tables, reservations, minimize_entropy=True)
    Optimizer.solve_problem()
    solution =  Optimizer.get_solution_json()
    return solution.get("pairings",{})