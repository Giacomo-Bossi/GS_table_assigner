import jsonschema
import json
from typing import TypeVar, List, Set
from solver_utils import Table, Reservation,Aggregate_reservation, Prog_id_gen
from error_types import *

T = TypeVar('T')


def transitive_closure(adjacency_sets: List[Set[T]]) -> List[Set[T]]:
        """Compute the transitive closure of the adjacency sets.

        This method merges any sets that have a non-empty intersection until no
        more merges are possible. The result is a list of sets where each set
        contains all items that are transitively connected to each other.
        Works for any hashable type T.
        """

        merged = True
        while merged:
            merged = False
            new_sets: List[Set[T]] = []
            while adjacency_sets:
                current_set = adjacency_sets.pop()
                merged_set = current_set.copy()
                for other_set in adjacency_sets:
                    if not merged_set.isdisjoint(other_set):
                        merged_set.update(other_set)
                        adjacency_sets.remove(other_set)
                        merged = True
                new_sets.append(merged_set)
            adjacency_sets = new_sets
        return adjacency_sets
    
    
class ILP_data_parser():
    def __init__(self,data):
        """
        Parse and validate input data for the ILP solver.It validates both the schema and the content of the data, ensuring that it is ready for use in the optimization process.
            Parameters
            ----------
        data : dict
            The input data to be parsed and validated, expected to conform to the schema defined in 'schemas\\input_schema.json'.
        """
        self.data = data.copy() 
        self.validate_data_schema(self.data)

        #check for data integrity issues such as duplicate table names or reservation names
        table_names = set()
        for tab in self.data["tables"]:
            tab["table_id"] = str(tab["table_id"]) # Ensure the table_id is a string for consistent handling
            if tab["table_id"] in table_names:
                raise Dupe_id_error(f"Duplicate table name found: {tab['table_id']}")
            table_names.add(tab["table_id"])


        groups_names = set()
        for res in self.data["groups"]:
            res["name"] = str(res["name"]) # Ensure the name is a string for consistent handling
            if res["name"] in groups_names:
                raise Dupe_id_error(f"Duplicate reservation name found: {res['name']}")
            groups_names.add(res["name"])

            #normalize the "close_to" field to always be a list of strings for consistent handling in later processing steps
            if res.get("close_to", None) is None:
                res["close_to"] = []
                continue
        
            if res.get("close_to", None) is not None:
                # Handle both single item and array
                close_to_value = res["close_to"]
                if isinstance(close_to_value, list):
                    res["close_to"] = [str(close) for close in close_to_value if close not in (None, "")]
                else:
                    res["close_to"] = [str(close_to_value)] if close_to_value not in (None, "") else []
        
        for res in self.data["groups"]:
            for close in res["close_to"]:
                if close == "":
                    continue
                if close not in groups_names:
                    error_msg = f"Found an undefined reference in a \"close_to\" field: \"{close}\", in reservation \"{res['name']}\" is nota group name."
                    raise Invalid_schema_error(error_msg)

        self.tables = None
        self.aggregated_reservations = None

    def extract_adjacency_sets(self)->list[set[str]]:
        """Extract adjacency sets from the input data.

        Each set contain one reservation and all other reservations in
        its ``close_to`` field. This method also checks for duplicate
        reservation names.

        Raises
        ------
        ValueError
            If duplicate reservation names are found in the input data or if a
            ``close_to`` field contains a reservation name that is not defined
            in the groups list.
        """
        sets = []
 
        for res in self.data["groups"]:
            
            close_to = res["close_to"]
            adjacency_set = set()
            adjacency_set.add(res["name"])

            for close in close_to:
                if close in adjacency_set:
                    pass
                adjacency_set.add(close)

            sets.append(adjacency_set)
        
        return sets
       
    def validate_data_schema(self,data):
        """
        Validate the input data against the predefined JSON schema.
            Raises
            ------
        jsonschema.exceptions.ValidationError    if the input data does not conform to the schema.
        """
        with open('v2\\celeryqueue\\Optimizer_engine\\schemas\\input_schema.json', 'r') as f:
            schema = json.load(f)
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            raise Invalid_schema_error(f"Input data does not conform to the required schema: {str(e)}") 
        #print("Data is valid.")
       
    def parse_tables(self):
        """
        parses and extracts a list of Table objects from the input data bind to the parser in the constructor.
        """
        # return cached tables if already parsed
        if self.tables is not None:
            return self.tables

        self.tables = []
        id_gen = Prog_id_gen()
        for tab in self.data["tables"]:
            self.tables.append(Table(tab, id_gen.get_next()))

        return self.tables
    
    def parse_reservations(self):
        # return cached aggregated reservations if already parsed
        if self.aggregated_reservations is not None:
            return self.aggregated_reservations

        adjacency_sets = self.extract_adjacency_sets()

        trans_closed_sets = transitive_closure(adjacency_sets)

        self.aggregated_reservations = []

        res_id_gen = Prog_id_gen()
        agg_res_id_gen = Prog_id_gen()

        for s in trans_closed_sets:
            res_list = []
            for res in self.data["groups"]:
                if res["name"] in s:
                    res_list.append(Reservation(res, res_id_gen.get_next()))
            self.aggregated_reservations.append(Aggregate_reservation(res_list, agg_res_id_gen.get_next()))

        return self.aggregated_reservations

if __name__ == "__main__":
    with open("v2\\celeryqueue\\Optimizer_engine\\Adjacent_test.json","r") as file:
        parser = ILP_data_parser(json.load(file))