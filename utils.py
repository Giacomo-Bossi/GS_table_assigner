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