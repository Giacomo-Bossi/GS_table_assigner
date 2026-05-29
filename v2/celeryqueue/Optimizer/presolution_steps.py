from solver_utils import Table, Reservation
from Table_problem_optimizer import Table_problem_optimizer

NEAR_FIELD_ATTR = "near_field"

def resize_tables_after_assignements(table_list, reservation_list, warnings_list, assignments):
    """
    utility function that resizes tables based on given assignements, to adapt tables for future steps.
    """ 
    for table_id in assignments.keys():
        assigned_reservations = assignments[table_id]
        
        if len(assigned_reservations) > 0:
            table = next((t for t in table_list if t.get_table_id() == table_id), None)
            capacity = next((t.get_capacity() for t in table_list if t.get_table_id() == table_id), None)
            
            if table is not None:
                total_assigned = sum(res.get_size() for res in reservation_list if res.get_name() in assigned_reservations)
                try:
                    table.resize(capacity - total_assigned)
                except ValueError as e:
                    raise ValueError(f"Error resizing table {table_id}: {str(e)}")
    return table_list


def preassign_close_to_field(table_list:list[Table], reservation_list:list[Reservation], warnings_list:list[str]):
    """
    presolver step that preassigns reservations with "close_to_field" requirement to tables with "close_to_field" attribute.
    """ 
    groups_to_preassign = [res for res in reservation_list if res.get_near_field()]
    field_tables = [table for table in table_list if table.get_near_field()]

    if len(field_tables) == 0 and len(groups_to_preassign) > 0:
        warnings_list.append(f"{len(groups_to_preassign)} reservations require {NEAR_FIELD_ATTR} but no tables have this attribute. Ignoring it")
        return
    
    Optimizer = Table_problem_optimizer(field_tables, groups_to_preassign, minimize_entropy=True)
    Optimizer.solve_problem()

    if not Optimizer.solution_available:
        warnings_list.append(f"Failed to find a solution during presolver step {preassign_close_to_field.__name__}, skipping preassignment.")
        return
    
    solution = Optimizer.get_solution_json()
    assignements = solution.get("pairings",{})
    return assignements

                    