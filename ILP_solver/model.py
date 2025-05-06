import json
import mip

def calculate_table_penalty(num_tables : int)->float:
    """
    assign the table penalty in a way that does not affect the number of people that can fit
    """
    return 1/(num_tables+1)

def solve_instance(tables :dict,guests:dict)->dict:
    """
    This function takes a json string describing tables and reservations and return a json string with the found solution to the problem
    
    """

    tables_ids = []
    tables_capacities = []
    for tab in tables:
        tables_ids.append(tab["id"])
        tables_capacities.append(tab["capacity"])

    groups_ids = []
    group_sizes = []

    for grp in guests:
        groups_ids.append(grp["id"])
        group_sizes.append(grp["size"])

    #for future, add preferences
    num_tables = len(tables)
    num_reserv = len(guests)

    table_penalty = calculate_table_penalty(num_tables)

    model = mip.Model(sense=mip.MAXIMIZE)

    assignement = [[model.add_var(var_type= mip.BINARY) for _ in tables_ids]for _ in groups_ids]#2D array with all variables
    used_tables = [model.add_var(var_type=mip.BINARY)for _ in tables_ids]

    #assign at most as the table capacity and linking constraint for used_tables
    for id in tables_ids:
        model.add_constr(mip.xsum(assignement[grp_id][id]*group_sizes[grp_id] for grp_id in groups_ids) <= tables_capacities[id])
        model.add_constr(mip.xsum(assignement[grp_id][id] for grp_id in groups_ids)<=num_tables * used_tables[id])


    #assign a group to at most one table
    for g_id in groups_ids:
        model.add_constr(mip.xsum(assignement[g_id][tab_id] for tab_id in tables_ids) <= 1)

    model.objective = mip.xsum(assignement[grp_id][tab_id]*group_sizes[grp_id] for tab_id in tables_ids for grp_id in groups_ids) - table_penalty * mip.xsum(used_tables)

    model.optimize()

    #organize optimal solution in json
    output_data = {"pairings": [],"used_tables" : 0}


    if model.num_solutions:
        table_assignments = {tab_id: [] for tab_id in range(len(tables_ids))}
        for grp_id in range(len(groups_ids)):
            for tab_id in range(len(tables_ids)):
                if assignement[grp_id][tab_id].x >= 0.99:
                    table_assignments[tab_id].append(grp_id)

        total_tables_used = sum(used_tables[i].x for i in range(len(used_tables)))

        output_data['pairings'] = table_assignments
        output_data['used_tables'] = int(total_tables_used)


    else:
        return {"Error : no solution is possible"}

    return output_data

def solve_instance_file(input_path:str, output_path:str)->bool:
    """
    Wrapper function for solve_instance() to use files for input/output
    """
    try:
        with open(input_path, 'r') as jsonfile:
            data = json.loads(jsonfile)
            sol = solve_instance(data['tables'],data['groups'])

            try :
                with open(output_path, 'w')as out:
                    out.write(json.dumps(sol).encode("utf-8"))
            except OSError:
                print("error while opening output file")
                return False
            
            return True
        
    except OSError:
        print("error while opening input file")
        return False


