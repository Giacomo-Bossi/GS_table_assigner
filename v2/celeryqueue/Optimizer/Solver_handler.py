from data_parser import ILP_data_parser
from error_types import *
class Solver_handler():
    
    def __init__(self,data):
        self.data = data
        self.warnings = []
        self.errors = []

        try:
            self.parser = ILP_data_parser(self.data)
        except ValueError as e:
            self.errors.append(str(e))

        try:
            self.tables = self.parser.parse_tables()
        except ValueError as e:
            self.errors.append(str(e))
        self.tables = self.parser.tables
        self.aggregated_reservations = self.parser.aggregated_reservations

