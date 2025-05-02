from typing import TextIO
import json
import copy

#checks that the IDS start form 0 and are incremented by 1 each time
def input_id_checker(tab_ids : list, grp_ids:list)->bool:
    expected = 0

    for i in range(len(tab_ids)):
        if tab_ids[i] != expected:
            return False
        expected+=1
    expected = 0

    for i in range(len(grp_ids)):
        if grp_ids[i] != expected:
            return False
        expected+=1
        
    return True


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
   

JSON_generate_input_file("input.json",[24,5,48],[4,23])

