import json
import mip

def calculate_table_penalty(num_tables : int)->float:
    """
    assign the table penalty in a way that does not affect the number of people that can fit
    """
    return 1/(num_tables+1)

def solve_instance(tables: dict, guests: dict) -> dict:
    

    # Compact index mapping
    T = list(range(len(tables)))
    G = list(range(len(guests)))

    tables_cap = [t["capacity"] for t in tables]
    group_sizes = [g["size"] for g in guests]

    num_tables = len(T)
    table_penalty = calculate_table_penalty(num_tables)

    model = mip.Model(sense=mip.MAXIMIZE, solver_name="cplex")

    # Variables
    assign = [[model.add_var(var_type=mip.BINARY)
               for j in T] for i in G]

    used = [model.add_var(var_type=mip.BINARY) for j in T]

    # Capacity constraints
    for j in T:
        model.add_constr(
            mip.xsum(assign[i][j] * group_sizes[i] for i in G)
            <= tables_cap[j]
        )

    # Linking (faster version)
    for j in T:
        model.add_constr(
            mip.xsum(assign[i][j] for i in G) >= used[j]
        )

    # Each group at most once
    for i in G:
        model.add_constr(
            mip.xsum(assign[i][j] for j in T) <= 1
        )

    # Objective
    model.objective = (
        mip.xsum(assign[i][j] * group_sizes[i] for i in G for j in T)
        - table_penalty * mip.xsum(used[j] for j in T)
    )

    model.optimize()

    # Output
    if not model.num_solutions:
        return {"error": "no solution"}

    table_assignments = {j: [] for j in T}
    for i in G:
        for j in T:
            if assign[i][j].x >= 0.99:
                table_assignments[j].append(i)

    return {
        "pairings": table_assignments,
        "used_tables": int(sum(used[j].x for j in T)),
        "total seats": sum(tables_cap),
        "total guests": sum(group_sizes),
        "total assignable": sum(
            group_sizes[i] for i in G
            if any(assign[i][j].x >= 0.99 for j in T)
        )
    }
