import json
import mip
from utils import input_id_checker

INPUT_FILE = "input.json"
OUTPUT_FILE = "output.json"

with open(INPUT_FILE, 'r') as f:
    data = json.load(f)

tables = data['tables']
guests = data['groups']

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


ok = input_id_checker(tables_ids,groups_ids)
if not ok:
    raise ValueError("Invalid table or group IDs in the input data.")

model = mip.Model(sense=mip.MAXIMIZE)

#Variables

assignement = [[model.add_var(var_type= mip.BINARY) for _ in tables_ids]for _ in groups_ids]#2D array with all variables

#table capacity contstraint
for id in tables_ids:
    model.add_constr(mip.xsum(assignement[grp_id][id]*group_sizes[grp_id] for grp_id in groups_ids) <= tables_capacities[id])


#single assignement
for g_id in groups_ids:
   model.add_constr(mip.xsum(assignement[g_id][tab_id] for tab_id in tables_ids) <= 1)

model.objective = mip.xsum(assignement[grp_id][tab_id]*group_sizes[grp_id] for tab_id in tables_ids for grp_id in groups_ids)

model.optimize()

output_data = []
if model.num_solutions:
    for grp_id in range(len(groups_ids)):
        for tab_id in range(len(tables_ids)):
            if assignement[grp_id][tab_id].x >= 0.99:
                print(f"Group {groups_ids[grp_id]} is assigned to table {tables_ids[tab_id]}")
                output_data.append({"group_id": grp_id, "table_id": tab_id, "group_size":group_sizes[grp_id]})
else:
    print("No solution found")


for line in output_data:
    with open(OUTPUT_FILE,'w') as f:
        json.dump(output_data, f, indent=2)


