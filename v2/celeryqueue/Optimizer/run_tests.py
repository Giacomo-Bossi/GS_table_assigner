from data_parser import ILP_data_parser, transitive_closure
import unittest
import json
import jsonschema
from error_types import *
from solver_utils import Table
import os
import glob

#this file tests the behaivor of the data parser, should be called from the repository root
class DataParserTestCase(unittest.TestCase): #TODO make test more robust
    
    def test_dupe_table_names(self):
        print("\nTesting duplicate table names...")
        with open("v2\\celeryqueue\\Optimizer\\tests\\duped_tables.json","r") as file:
            warnings_list = []
            ILP_data_parser(json.load(file), warnings_list=warnings_list)
            assert any("Duplicate table_id '1' renamed to '1_1'." in warning for warning in warnings_list)
            
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
    
    