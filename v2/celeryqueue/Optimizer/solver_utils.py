from mnemonics import *

class Table():
    def __init__(self,table:dict,prog_id:int=0):
        self.table_id = str(table[TABLE_ID_ATTR])
        self.capacity = table[TABLE_CAPACITY_ATTR]
        self.head_seats = int(int(table.get("head_seats", 0))!=0)
        self.model_id = prog_id
        self.original_dict = table.copy()  #keeping full table description to allow to custom logic to be added in presolver steps
        self.near_field = table.get(TABLE_NEAR_FIELD_ATTR, False)

    def get_table_id(self)->str:
        return self.table_id
    def get_capacity(self)->int:
        return self.capacity
    def get_head_seats(self)->int:
        return self.head_seats
    def get_model_id(self)->int:
        return self.model_id
    def get_original_dict(self)->dict:
        return self.original_dict
    def get_near_field(self)->bool:
        return self.near_field
    def set_model_id(self,new_id:int):
        self.model_id = new_id
    def set_head_seat(self,head_seat:bool):
        self.head_seats = int(head_seat)
    def copy(self):
        return Table(self.original_dict,self.model_id)
    def resize(self,new_capacity:int):
        """changes the table capacity if manual assignements or presolver steps require it
        """
        if new_capacity < self.capacity and new_capacity >= 0:
            self.capacity = new_capacity
        else:
            raise ValueError(f"New capacity {new_capacity} is greater than current capacity {self.capacity}, resizing not allowed.")
        
    
class Reservation():          
    def __init__(self,reservation:dict,prog_id:int=0,warnings_list:list[str]=None):
            self.name = str(reservation[RESERVATION_NAME_ATTR])
            self.size = reservation[RESERVATION_SIZE_ATTR]
            self.require_head = reservation.get(RESERVATION_REQUIRE_HEAD_ATTR,0)
            self.model_id = prog_id
            #self.original_dict = reservation.copy() #keeping full reservation description to allow to custom logic to be added in presolver steps
            self.near_field = reservation.get(RESERVATION_NEAR_FIELD_ATTR, False)
    def get_name(self)->str:
        return self.name
    def get_size(self)->int:
        return self.size
    def get_require_head(self)->bool:
        return self.require_head
    def get_model_id(self)->int:
        return self.model_id
    def get_near_field(self)->bool:
        return self.near_field
    def set_model_id(self,new_id:int):
        self.model_id = new_id
    def set_require_head(self,require_head:bool):
        self.require_head = require_head
    def set_near_field(self,near_field:bool):
        self.near_field = near_field
    def split(self):
        """
        Defines how to split a reservation if it cannot be assigned to a single table.
        """ 
        pass

class Aggregate_reservation(Reservation):
    def __init__(self,reservations:list[Reservation],prog_id:int=0,warnings_list:list[str]=None):
        self.reservations = reservations.copy()
        self.name = "+".join([res.get_name() for res in reservations])
        self.size = sum([res.size for res in reservations])
        self.require_head = any([res.require_head for res in reservations]) 
        #self.original_dict = reservations.copy() #TODO think
        if warnings_list is not None:
            head_count = sum(1 for res in reservations if res.get_require_head())
            if head_count > 1:
                warnings_list.append(f"Aggregate reservation '{self.name}' contains {head_count} reservations requiring head seats,\
                                      only one will be honored.")
        self.near_field = any([res.get_near_field() for res in reservations])
        self.model_id = prog_id
    #@override
    def split(self):
        """
        Defines how to split a reservation if it cannot be assigned to a single table.
        """ 
        pass

class Prog_id_gen():
    def __init__(self):
        self.curr_id = 0
    def get_next(self):
        ret = self.curr_id
        self.curr_id+=1
        return ret


