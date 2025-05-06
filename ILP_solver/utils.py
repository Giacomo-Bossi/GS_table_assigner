import json
from model import solve_instance
#checks that the IDS start form 0 and are incremented by 1 each time
#def input_id_checker(tab_ids : list, grp_ids:list)->bool:
    
#    for i, item in enumerate(tab_ids):
#        if item.get('id') != i:
#            print(f"tab_ids: {item} expected: {i}")
#            return False

#    for i, item in enumerate(grp_ids):
#        if item.get('id') != i:
#            print(f"grp_ids: {item} expected: {i}")
#            return False
        
#    return True


def JSON_add_table(capacity: int,id_counter:int,jsonstring:dict) -> dict:
    """
    Updates the jsonstring by adding the specified table
    """
    tables = jsonstring['tables']
    tables.append({"id" : id_counter,  "capacity": capacity})
    jsonstring['tables'] = tables
    return jsonstring

def JSON_add_reservation(size : int,id_counter:int,jsonstring:dict)->dict:
    """
    Updates the jsonstring by adding the specified reservation 
    """
    res =jsonstring['groups']
    res.append({"id" : id_counter,  "size": size})
    jsonstring['groups'] = res
    return jsonstring

def JSON_generate_input(table_list:list,reservation_list:list)->dict:
    """
    Generates a dictionary with tables and reservations, it can be transaled directly in a json string.
    The dictionary is always compatible with the solver.
    Args:
        tables (list[int]): A list of integers representing table capacities.
        reservations (list[int]): A list of integers representing reservation sizes.
    Returns:
        The dictionary to feed to the model
    """
    TABLE_COUNT = 0
    RESERVATION_COUNT = 0
    JSONSTRING = {"tables": [],"groups": []}

    for capacity in table_list:
        JSONSTRING=JSON_add_table(capacity,TABLE_COUNT,JSONSTRING)
        TABLE_COUNT+=1

    for size in reservation_list:
        JSONSTRING = JSON_add_reservation(size,RESERVATION_COUNT,JSONSTRING)
        RESERVATION_COUNT+=1

    return JSONSTRING

def JSON_generate_input_file(filename: str, tables_list: list[int], reservations_list: list[int]) -> bool:
    """
    Generates a JSON string with the input for the model and writes it to a file.
    Args:
        filename (str): The path to the JSON file to be created.
        tables (list[int]): A list of integers representing table capacities.
        reservations (list[int]): A list of integers representing reservation sizes.
    Returns:
        bool: True if the file was successfully created, False if an error occurred.
    Notes:
        - The function writes the JSON data to the specified file.
        - If an OSError occurs (e.g., file cannot be opened), the function prints an error message and returns False.
    """
    try:
        with open(filename, 'w') as jsonfile:
            json_string = JSON_generate_input(tables_list,reservations_list)           
            jsonfile.write(json.dumps(json_string))
            return True
        
    except OSError:
        print("error while opening the file")
        return False
   

#JSON_generate_input_file("input.json",[24,5,48],[4,23])

def generate_table_mapping(tables:list)->dict:
    """
    maps the tables id to a progressive index used by the solver
    """
    dic = {}
    for id, tab in enumerate(tables):
        dic[id] = tab['table_id']

    return dic



def generate_groups_mapping(groups:list)->dict:
    """
    maps the groups names to a progressive index used by the solver
    """
    dic = {}
    for id, grp in enumerate(groups):
        dic[id] = grp['name']

    return dic

def generate_mapped_tables(inv_map : dict,tab_list:list)-> list:
    ret = []
    for tab in tab_list:
        base = {"id":0,"capacity":0,"head_seats":0}
        base['id'] = inv_map[tab['table_id']]
        base['capacity'] = tab['capacity']
        if tab.get('head_seats'):
            base['head_seats'] = tab['head_seats']
        ret.append(base)
    
    return ret

def generate_mapped_groups(inv_map:dict,grp_list)->list:
    ret = []
    for grp in grp_list:
        base = {"id":0 , "size": 0, "required_head":0}
        base['id'] = inv_map[grp['name']]
        base['size'] = grp['size']
        if grp.get('required_head'):
            base['required_head'] = 1 if grp['required_head'] else 0
        ret.append(base)
    return ret

def remap_out(model_out : dict,tab_map,grp_map):
    pairs = model_out['pairings']
    remapped_dic = {}
    for t_id in pairs:
        remapped_dic[tab_map[t_id]] = []
        for g_id in pairs[t_id]:
            remapped_dic[tab_map[t_id]].append(grp_map[g_id])

    model_out['pairings'] = remapped_dic
    return model_out

#input must have already been validated
def process_request(json_input : dict)->dict:
    """
    process the input to work with incremental indexes and constuct maps to invert the process at the end
    """
    tab_list = json_input['tables']
    grp_list = json_input['groups']

    tab_id_map = generate_table_mapping(tab_list)
    inverse_tab_id_map = {v: k for k, v in tab_id_map.items()}  #consider changing to bidict

    grp_id_map = generate_groups_mapping(grp_list)
    inverse_grp_id_map = {v: k for k, v in grp_id_map.items()}

    map1 = generate_mapped_tables(inverse_tab_id_map,tab_list)

    map2 = generate_mapped_groups(inverse_grp_id_map,grp_list)

    model_out = solve_instance(map1,map2)  #heads still not supported
    
    return remap_out(model_out,tab_id_map,grp_id_map)