from solver_utils import Table, Reservation
from Table_problem_optimizer import Table_problem_optimizer, calculate_lambda_coeff

NEAR_FIELD_ATTR = "near_field"
def res_list_remove_by_name(reservation_list:list[Reservation], name:str):
    reservation_list[:] = [res for res in reservation_list if res.get_name() != name]
    return

def table_list_remove_by_id(table_list:list[Table], table_id:str):
    table_list[:] = [tab for tab in table_list if tab.get_table_id() != table_id]
    return

def get_table_controid(table:Table):
    table_dict = table.get_original_dict()
    gui_dict = table_dict.get("gui",{})
    if gui_dict == {}:
        raise ValueError(f"Table {table.get_table_id()} does not have gui coordinates, cannot calculate centroid.")
    
    centroid = (gui_dict.get("x",0)+gui_dict.get("height",0)/2, gui_dict.get("y",0)+gui_dict.get("width",0)/2)
    return centroid

def table_distance(table1:Table, table2:Table):
    centroid1 = get_table_controid(table1)
    centroid2 = get_table_controid(table2)

    distance = ((centroid1[0] - centroid2[0]) ** 2 + (centroid1[1] - centroid2[1]) ** 2) ** 0.5
    return distance

def get_closest(table:Table, table_list:list[Table]):
   
    if len(table_list) == 0:
        return None
    table_dict = table.get_original_dict()
    gui_dict = table_dict.get("gui",{})
       
    centroid = get_table_controid(table)

    min_distance = float("inf")
    closest_table = None
    for tab in table_list:
        if tab.get_table_id() != table.get_table_id():
            tab_centroid = get_table_controid(tab)

            distance = table_distance(table, tab)
            if distance < min_distance:
                min_distance = distance
                closest_table = tab

    return closest_table

def update_state_from_Optimizer_pairings(table_list:list[Table], reservation_list:list[Reservation], warnings_list:list[str],\
                 assignements:dict[str,list[str]],new_assignments:dict[str,list[str]]):

    for table_id, res_list in new_assignments.items():
        for res_name in res_list:

            tab = next((t for t in table_list if t.get_table_id() == table_id), None)
            if tab is None:
                raise ValueError(f"Table with id {table_id} not found in table list.")
            
            res = next((r for r in reservation_list if r.get_name() == res_name), None)
            if res is None:
                raise ValueError(f"Reservation with name {res_name} not found in reservation list.")
            
            assignements[table_id].append(res_name)
            res_list_remove_by_name(reservation_list, res_name)

            tab.resize(tab.get_capacity() - res.get_size())
            if res.get_require_head():
                tab.set_head_seat(tab.set_head_seat(False))
            

def preassign_close_to_field(table_list:list[Table], reservation_list:list[Reservation], warnings_list:list[str],\
                             assignements:dict[str,list[str]]):
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
         #not enough haed seats to satisfy the requirement
        warnings_list.append(f"{len(groups_to_preassign)} reservations require {NEAR_FIELD_ATTR} and head seats,\
                              but not enough tables with {NEAR_FIELD_ATTR} have head seats.\
                              Ignoring {NEAR_FIELD_ATTR} requirement for these reservations.")
        
        for res in groups_to_preassign:
            if res.get_near_field():
                res.set_near_field(False)
                groups_to_preassign.remove(res)

    #assign with optimizer
    Optimizer = Table_problem_optimizer(field_tables, groups_to_preassign, minimize_entropy=True)
    Optimizer.solve_problem()

    if not Optimizer.solution_available:
        warnings_list.append(f"Failed to find a solution during presolver step {preassign_close_to_field.__name__}, skipping preassignment.")
        return
    
    solution = Optimizer.get_solution_json()
    new_assignements = solution.get("pairings",{})
    print(new_assignements)
    update_state_from_Optimizer_pairings(table_list, reservation_list, warnings_list, assignements, new_assignements)

    return 

def split_massive_reservations(table_list:list[Table], reservation_list:list[Reservation], warnings_list:list[str],\
                             assignements:dict[str,list[str]]):
    """
    presolver step that splits reservations that are larger than any table capacity into smaller reservations.
    """ 
    max_capacity = max(table.get_capacity() for table in table_list)
    max_head_capacity = max(table.get_capacity() for table in table_list if table.get_head_seats() > 0)
    head_tables = [table for table in table_list if table.get_head_seats() > 0]

    big_res = [res for res in reservation_list if res.get_size() > max_capacity \
                  or (res.get_require_head() and res.get_size() > max_head_capacity)]
    
    # sort big reservations by size descending so largest are split first
    big_res.sort(key=lambda r: r.get_size(), reverse=True)
       
    while len(big_res) > 0:  #TODO should we assign the require_head first ?
        current_res = big_res[0]

        #try to split
        if current_res.get_require_head(): 
            new_groups = current_res.split(max_head_capacity)
        else:
            new_groups = current_res.split(max_capacity)

        if not new_groups:
            res_list_remove_by_name(reservation_list, current_res.get_name()) #won't be assigned ever since it can't fit neither split
            warnings_list.append(f"Failed to split reservation {current_res.get_name()} with size {current_res.get_size()}. Ignoring it completely.")
            continue
            
        if current_res.get_require_head():
           biggest_table = max(head_tables,key=lambda table: table.get_capacity(), default=None)
        else:
            biggest_table = max(table_list, key=lambda table: table.get_capacity())

        new_big_group = max(new_groups, key=lambda res: res.get_size())
        new_small_group = min(new_groups, key=lambda res: res.get_size())

        biggest_table.resize(biggest_table.get_capacity() - new_big_group.get_size())

        if current_res.get_require_head(): #TODO fix hidden assumption that biggest group inherits head
            biggest_table.set_head_seat(False)
            
        assignements[biggest_table.get_table_id()].append(new_big_group.get_name())

        closest_to_biggest_table = get_closest(biggest_table, table_list)

        if closest_to_biggest_table is None:
            warnings_list.append(f"Failed to find a closest table to {biggest_table.get_table_id()} for split reservation\
                                  {new_small_group.get_name()}. Assigning it to any table with enough capacity.")
            closest_to_biggest_table = next((tab for tab in table_list if tab.get_capacity() >= new_small_group.get_size()), None)

            if closest_to_biggest_table is None:
                raise ValueError(f"No table with enough capacity to assign split reservation {new_small_group.get_name()}\
                                  with size {new_small_group.get_size()}.")

        if closest_to_biggest_table.get_capacity() < new_small_group.get_size():
            reservation_list.extend(new_groups)
            warnings_list.append(f"Failed to assign split reservation {new_small_group.get_name()} with size {new_small_group.get_size()}\
                                  to closest table {closest_to_biggest_table.get_table_id()} with capacity {closest_to_biggest_table.get_capacity()}.\
                                  Will be put somewhere else.")

        else:
            closest_to_biggest_table.resize(closest_to_biggest_table.get_capacity() - new_small_group.get_size())
            assignements[closest_to_biggest_table.get_table_id()].append(new_small_group.get_name())

        res_list_remove_by_name(reservation_list, current_res.get_name())
        
        max_capacity = max(table.get_capacity() for table in table_list)
        max_head_capacity = max(table.get_capacity() for table in table_list if table.get_head_seats() > 0)
        head_tables = [table for table in table_list if table.get_head_seats() > 0]
        big_res = [res for res in reservation_list if res.get_size() > max_capacity \
                  or (res.get_require_head() and res.get_size() > max_head_capacity)]
    
    #end while

def run_solver_final(tables:list[Table], reservations:list[Reservation], warnings_list:list[str],\
                     assignements:dict[str,list[str]]):
    """
    runs the solver with the remaining tables and reservations.
    """ 
    Optimizer = Table_problem_optimizer(tables, reservations, minimize_entropy=True)
    Optimizer.solve_problem()
    solution =  Optimizer.get_solution_json()
    update_state_from_Optimizer_pairings(tables, reservations, warnings_list, assignements, solution.get("pairings",{}))
    return