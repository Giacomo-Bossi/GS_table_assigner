import json
from model import solve_instance

def JSON_generate_input(table_capacities: list, group_sizes: list)->dict:
    data = {
        "tables": [{"table_id": f"table_{i+1}", "capacity": cap} for i, cap in enumerate(table_capacities)],
        "groups": [{"name": f"group_{i+1}", "size": size} for i, size in enumerate(group_sizes)]
    }
    return data

def JSON_generate_input_file(filename: str, table_capacities: list, group_sizes: list):
    """
    Generates a JSON file according to the input schema.

    Args:
        filename (str): The name of the file to save the JSON.
        table_capacities (list): A list of integers representing table capacities.
        group_sizes (list): A list of integers representing group sizes.
    """
    data = JSON_generate_input(table_capacities,group_sizes)

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


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
