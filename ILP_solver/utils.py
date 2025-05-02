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

TABLE_COUNT = 0
RESERVATION_COUNT = 0
JSONSTRING = {"tables": [],"groups": []}

def JSON_add_table(capacity: int = 1) -> None:
    """
    Adds a table to the json string, handles ID by itself
    """
    global TABLE_COUNT
    global JSONSTRING
    tables = JSONSTRING['tables']
    tables.append({"id" : TABLE_COUNT,  "capacity": capacity})
    TABLE_COUNT+=1
    JSONSTRING['tables'] = tables

def JSON_add_reservation(size : int=1)->None:
    """
    Adds a reservation to the json string, handles ID by itself
    """
    global RESERVATION_COUNT
    global JSONSTRING
    res =JSONSTRING['groups']
    res.append({"id" : RESERVATION_COUNT,  "size": size})
    RESERVATION_COUNT+=1
    JSONSTRING['groups'] = res

def JSON_INIT()->None:
    """
    Restore initial values of  global variables used when generating a json
    """
    global TABLE_COUNT
    global RESERVATION_COUNT
    global JSONSTRING
    TABLE_COUNT = 0
    RESERVATION_COUNT = 0
    JSONSTRING = {"tables": [],"groups": []}


def JSON_generate_input(filename: str, tables_list: list[int], reservations_list: list[int]) -> bool:
    """
    Generates a JSON input file for table and reservation data.
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
            JSON_INIT()
            for capacity in tables_list:
                JSON_add_table(capacity)
            for size in reservations_list:
                JSON_add_reservation(size)
            
            jsonfile.write(json.dumps(JSONSTRING))
            return True
        
    except OSError:
        print("error while opening the file")
        return False
            
JSON_generate_input("input.json",[24,5,48],[4,22])
