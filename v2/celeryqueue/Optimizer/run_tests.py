from data_parser import ILP_data_parser, transitive_closure
from Solver_handler import Solver_handler
from presolution_steps import *
import unittest
import json
import jsonschema
from error_types import *
from solver_utils import *
import os
import glob
from mnemonics import *


#this file tests the behaivor of the data parser, should be called from the repository root

class DataParserTestCase(unittest.TestCase): #TODO make tests more robust
    
    def test_dupe_table_names(self):
        print("\nTesting duplicate table names...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\duped_tables.json","r") as file:
            warnings_list = []
            parser = ILP_data_parser(json.load(file), warnings_list=warnings_list)
            assert len(warnings_list) > 0
            tables = parser.parse_tables()
            table_ids = [t.table_id for t in tables]
            assert len(table_ids) == len(set(table_ids)) #check for unique table ids after parsing
            assert "1" in table_ids
            assert "1_1" in table_ids
            
    def test_dupe_reservation_names(self):
        print("\nTesting duplicate reservation names...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\duped_reservation.json","r") as file:
            warnings_list = []
            ILP_data_parser(json.load(file), warnings_list=warnings_list)
            assert len(warnings_list) > 0

    def test_invalid_schema(self):
        print("\nTesting invalid schema...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\invalid_schema.json","r") as file:
            with self.assertRaises(Invalid_schema_error):
                ILP_data_parser(json.load(file))

    def test_parse_tables(self): 
        print("\nTesting table parsing...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\Adjacent_test.json","r") as file:
            parser = ILP_data_parser(json.load(file))
            tables = parser.parse_tables()
            self.assertEqual(len(tables), 26)

    def test_extract_adjacency_sets(self):
        print("\nTesting adjacency set extraction...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\Adjacent_test.json","r") as file:
            parser = ILP_data_parser(json.load(file))
            adjacency_sets = parser.extract_adjacency_sets()
            expected_sets = [{'2326'}, {'2326', '2328'}, {'2329'}] 
            self.assertEqual(len(adjacency_sets), len(expected_sets))
            for s in expected_sets:
                self.assertIn(s, adjacency_sets)
            for s in adjacency_sets:
                self.assertIn(s, expected_sets)

    def test_parse_reservations(self):
        print("\nTesting reservation parsing and aggregation...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\Adjacent_test.json","r") as file:
            parser = ILP_data_parser(json.load(file))
            reservations = parser.parse_reservations()
            expected_names = {"2326+2328", "2329"}
            self.assertEqual(len(reservations), len(expected_names))
            for res in reservations:
                self.assertIn(res.name, expected_names)
            for name in expected_names:
                self.assertIn(name, [res.name for res in reservations])
            size_2326 = 1
            size_2328 = 3
            size_2329 = 4
            assert any(res.size == size_2326 + size_2328 and res.name == "2326+2328" for res in reservations)
            assert any(res.size == size_2329 and res.name == "2329" for res in reservations)
    
    def test_split_reservation(self):
        print("\nTesting reservation splitting...")
        res = Reservation({RESERVATION_NAME_ATTR: "test_res", RESERVATION_SIZE_ATTR: 5}, prog_id=0)
        max_capacity = 3
        children = res.split(max_capacity)
        assert len(children) == 2
        assert children[0].get_size() == 3
        assert children[1].get_size() == 2
        assert children[0].get_name() == "test_res-part1"
        assert children[1].get_name() == "test_res-part2"

    def test_split_reservation_no_split(self):
        print("\nTesting reservation splitting with no split needed...")
        res = Reservation({RESERVATION_NAME_ATTR: "test_res", RESERVATION_SIZE_ATTR: 2}, prog_id=0)
        max_capacity = 3
        children = res.split(max_capacity)
        assert len(children) == 1
        assert children[0].get_size() == 2
        assert children[0].get_name() == "test_res-part1"

    def test_split_on_aggregate_reservation(self):
        print("\nTesting splitting on aggregate reservation...")
        res1 = Reservation({RESERVATION_NAME_ATTR: "res1", RESERVATION_SIZE_ATTR: 2}, prog_id=0)
        res2 = Reservation({RESERVATION_NAME_ATTR: "res2", RESERVATION_SIZE_ATTR: 3}, prog_id=0)
        
        agg_res = Aggregate_reservation([res1, res2], prog_id=0)
        max_capacity = 4
        
        children = agg_res.split(max_capacity)
        assert len(children) == 2
        # assert that split divides in the indended way
        assert any(c.get_size() == 3 for c in children)
        assert any(c.get_size() == 2 for c in children)

    def test_split_on_aggregate_reservation_no_split(self):
        print("\nTesting splitting on aggregate reservation with no split needed...")
        res1 = Reservation({RESERVATION_NAME_ATTR: "res1", RESERVATION_SIZE_ATTR: 2}, prog_id=0)
        res2 = Reservation({RESERVATION_NAME_ATTR: "res2", RESERVATION_SIZE_ATTR: 1}, prog_id=0)
        
        agg_res = Aggregate_reservation([res1, res2], prog_id=0)
        
        max_capacity = 4
        
        children = agg_res.split(max_capacity)
        assert len(children) == 1
        assert children[0].get_size() == 3

    def test_split_aggregate_split_groups(self):
        print("\nTesting splitting on aggregate reservation with split groups...")
        res1 = Reservation({RESERVATION_NAME_ATTR: "res1", RESERVATION_SIZE_ATTR: 5}, prog_id=0)
        res2 = Reservation({RESERVATION_NAME_ATTR: "res2", RESERVATION_SIZE_ATTR: 3}, prog_id=0)
            
        agg_res = Aggregate_reservation([res1, res2, ], prog_id=0)
        
        max_capacity = 4
        
        children = agg_res.split(max_capacity)
        for child in children:
            print(child)  #TODO check logic
       

    def test_preassign_close_to_field(self):
        print("\nTesting preassign_close_to_field presolver step...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\close_to_field_test.json","r") as file:
            parser = ILP_data_parser(json.load(file))
            tables = parser.parse_tables()
            tables_copy = tables.copy() 

            reservations = parser.parse_reservations()
            warnings_list = []
            assignments = {"1": [], "2": [], "3": [], "2_1": []} #usually done by Solver_handler
            preassign_close_to_field(tables, reservations, warnings_list,assignments)

            assert len(warnings_list) == 0
            assert len(assignments) > 0
            for table_id, res_names_list in assignments.items():
                if res_names_list: #only check assigned tables
                    table_after = next((t for t in tables if t.get_table_id() == table_id), None)
                    table_before = next((t for t in tables_copy if t.get_table_id() == table_id), None)
                    assert table_before is not None
                    assert table_after is not None
                    assert table_after.get_near_field() == True
                    assert table_after.get_capacity() <= table_before.get_capacity()
                    for res_name in res_names_list:
                        res = next((r for r in reservations if r.get_name() == res_name), None)
                        assert res is None #is assigned then should be removed from reservation list
                        
    def test_get_closest(self):
        print("\nTesting get_closest function...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\test_with_gui.json","r") as file:
            parser = ILP_data_parser(json.load(file))
            tables = parser.parse_tables()
            table_1 = next((t for t in tables if t.get_table_id() == "1"), None)
            closest_to_1 = get_closest(table_1, tables)
            assert closest_to_1 is not None
            distance_to_closest = table_distance(table_1, closest_to_1)

            for t in tables:
                if t.get_table_id() != "1":
                    distance_to_1 = table_distance(table_1, t)
                    assert distance_to_closest <= distance_to_1

            
            assert closest_to_1.get_table_id() == "2" #based on the test json, table 2 is the closest to table 1
            assert get_closest(next((t for t in tables if t.get_table_id() == "10"), None), tables).get_table_id() == "11" #table 11 is the closest to table 10 based on the test json
            assert get_closest(next((t for t in tables if t.get_table_id() == "17"), None), tables).get_table_id() == "18" #table 5 or 6 could be closest if horizontal tables are not handled correctly, but 18 is the closest if they are handled correctly

    def test_split_massive(self):
        print("\nTesting splitting of a massive reservation...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\test_with_gui.json","r") as file:
            parser = ILP_data_parser(json.load(file))
            reservations = parser.parse_reservations()
            tables = parser.parse_tables()
            warnings_list = []
            assignments = {t.get_table_id(): [] for t in tables}
            capacities = {t.get_table_id(): t.get_capacity() for t in tables}
            
            split_massive_reservations(tables, reservations, warnings_list, assignments)
            
            new_capacities = {t.get_table_id(): t.get_capacity() for t in tables}
            assigned_tables = [table_id for table_id, res_list in assignments.items() if res_list]
            assert len(assigned_tables) > 1
            for table_id, res_list in assignments.items():
                if res_list:  # only check tables that got assigned reservations
                    assert new_capacities[table_id] < capacities[table_id]
                    

            print(assignments)





"""
------------------------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------- END TESTS ---------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------------
"""

def prettyfy_test_jsons(verbose=False):
    test_dir = "v2\\celeryqueue\\Optimizer\\tests"
    json_files = glob.glob(os.path.join(test_dir, "*.json"))

    for json_file in json_files:
        if verbose:
            print(f"\n--- prettyfying {os.path.basename(json_file)} ---")
        # Read, pretty-format and overwrite the JSON file
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        pretty = json.dumps(data, indent=2, ensure_ascii=False)
        with open(json_file, "w", encoding="utf-8") as file:
            file.write(pretty + "\n")
       


if __name__ == "__main__":
    unittest.main(exit=False)
    prettyfy_test_jsons(verbose=False)
    
    