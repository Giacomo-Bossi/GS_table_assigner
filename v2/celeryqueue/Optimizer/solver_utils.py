from Optimizer.mnemonics import *

class Table():
    def __init__(self,table:dict,prog_id:int=0):
        self.table_id = str(table[TABLE_ID_ATTR])
        self.capacity = table[TABLE_CAPACITY_ATTR]
        self.head_seats = int(int(table.get("head_seats", 0))!=0)
        self.model_id = prog_id
        self.original_dict = table.copy()  #keeping full table description to allow to custom logic to be added in presolver steps
        # "near_field" moved inside a "tags" object: prefer tags[TABLE_NEAR_FIELD_ATTR]
        tags = table.get("tags") or {}
        self.near_field = tags.get(TABLE_NEAR_FIELD_ATTR, table.get(TABLE_NEAR_FIELD_ATTR, False))

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
    
    def print_info(self):
        print(
            f"Table(table_id={self.table_id}, capacity={self.capacity}, head_seats={self.head_seats}, "
            f"near_field={self.near_field}, model_id={self.model_id})"
        )

    def __str__(self):
        return (
            f"Table(table_id={self.table_id}, capacity={self.capacity}, head_seats={self.head_seats}, "
            f"near_field={self.near_field}, model_id={self.model_id})"
        )
    
    def resize(self,new_capacity:int):
        """changes the table capacity if manual assignements or presolver steps require it
        """
        if new_capacity <= self.capacity and new_capacity >= 0:
            self.capacity = new_capacity
        else:
            raise ValueError(
                "New capacity {} is invalid for current capacity {}, resizing not allowed."
                .format(new_capacity, self.capacity)
            )
        
    
class Reservation():          
    def __init__(self,reservation:dict,prog_id:int=0,warnings_list:list[str]=None):
            self.name = str(reservation[RESERVATION_NAME_ATTR])
            self.size = reservation[RESERVATION_SIZE_ATTR]
            self.require_head = reservation.get(RESERVATION_REQUIRE_HEAD_ATTR,0)
            self.model_id = prog_id
            self.original_dict = reservation.copy() #keeping full reservation description to allow to custom logic to be added in presolver steps
            self.near_field = reservation.get(RESERVATION_NEAR_FIELD_ATTR, False)
            self.show_name = reservation.get(RESERVATION_SHOW_NAME_ATTR, self.name)
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
    def get_dict(self)->dict:
        return {
            RESERVATION_NAME_ATTR: self.name,
            RESERVATION_SHOW_NAME_ATTR: self.show_name, 
            RESERVATION_SIZE_ATTR: self.size, 
            RESERVATION_REQUIRE_HEAD_ATTR: self.require_head, 
            RESERVATION_NEAR_FIELD_ATTR: self.near_field
        }
    def set_model_id(self,new_id:int):
        self.model_id = new_id
    def set_require_head(self,require_head:bool):
        self.require_head = require_head
    def set_near_field(self,near_field:bool):
        self.near_field = near_field

    def print_info(self):
        print(
            f"Reservation(name={self.name}, size={self.size}, require_head={self.require_head}, "
            f"near_field={self.near_field}, model_id={self.model_id})"
        )

    def __str__(self):
        return (
            f"Reservation(name={self.name}, size={self.size}, require_head={self.require_head}, "
            f"near_field={self.near_field}, model_id={self.model_id})"
        )
    
    def split(self,max_capacity:int):
        """
        Defines how to split a reservation if it cannot be assigned to a single table.
        """ 
        sizes = (max_capacity,self.size - max_capacity) if self.size > max_capacity else (self.size,)

        childrens: list[Reservation] = []
        for i, s in enumerate(sizes, start=1):
            new_dict = self.original_dict.copy()
            new_dict[RESERVATION_SIZE_ATTR] = s
            new_dict[RESERVATION_REQUIRE_HEAD_ATTR] = self.require_head if i == 1 else 0
            
            try:
                base_name = str(new_dict.get(RESERVATION_NAME_ATTR, self.name))
            except Exception:
                base_name = self.name

            new_dict[RESERVATION_NAME_ATTR] = f"{base_name}-part{i}"
            childrens.append(Reservation(new_dict, prog_id=self.model_id))
            
        return childrens

class Aggregate_reservation(Reservation):
    def __init__(self,reservations:list[Reservation],prog_id:int=0,warnings_list:list[str]=None):
        self.reservations = reservations.copy()
        self.name = "+".join([res.get_name() for res in reservations])
        self.size = sum([res.size for res in reservations])
        self.require_head = any([res.require_head for res in reservations]) 
        self.original_dicts = reservations.copy()
        if warnings_list is not None:
            head_count = sum(1 for res in reservations if res.get_require_head())
            if head_count > 1:
                warnings_list.append(f"Aggregate reservation '{self.name}' contains {head_count} reservations requiring head seats,\
                                      only one will be honored.")
        self.near_field = any([res.get_near_field() for res in reservations])
        self.model_id = prog_id
        self.reservation_dicts = [res.get_dict() for res in reservations]

    #@override
    def split(self, max_capacity:int): #TODO check
        """
        Defines how to split an aggregate reservation into parts that fit within
        max_capacity. Behavior:
        - If aggregate contains a single Reservation, delegate to that Reservation.split(max_capacity).
        - Otherwise, try to pack reservations into subsets (greedy first-fit) so that
          each subset total size <= max_capacity. Reservations larger than max_capacity
          are split using their own split method.
        Returns a list of Reservation or Aggregate_reservation instances.
        """
        if len(self.reservations) == 0:
            return []

        # If single child, delegate
        if len(self.reservations) == 1:
            child = self.reservations[0]
            return child.split(max_capacity)

        # Prepare list of reservations to pack, splitting oversized ones first
        to_pack: list[Reservation] = []
        for res in self.reservations:
            if res.get_size() > max_capacity:
                # split oversized reservation into parts
                parts = res.split(max_capacity)
                to_pack.extend(parts)
            else:
                to_pack.append(res)

        groups: list[list[Reservation]] = []
        # Greedy first-fit packing into groups
        for res in to_pack:
            placed = False
            for grp in groups:
                if sum(r.get_size() for r in grp) + res.get_size() <= max_capacity:
                    grp.append(res)
                    placed = True
                    break
            if not placed:
                groups.append([res])

        # Convert groups to Aggregate_reservation when group contains >1 reservation,
        # otherwise return the single Reservation
        result: list[Reservation] = []
        for grp in groups:
            if len(grp) == 1:
                result.append(grp[0])
            else:
                agg = Aggregate_reservation(grp, prog_id=self.model_id)
                result.append(agg)

        return result
    

    #@override
    def get_dict(self)->dict:
        return {
            RESERVATION_NAME_ATTR: self.name,
            RESERVATION_SIZE_ATTR: self.size, 
            RESERVATION_REQUIRE_HEAD_ATTR: self.require_head, 
            RESERVATION_NEAR_FIELD_ATTR: self.near_field,
            AGGREGATE_RESERVATIONS_SUB_LIST_ATTR: self.reservation_dicts
        }
        

class Prog_id_gen():
    def __init__(self):
        self.curr_id = 0
    def get_next(self):
        ret = self.curr_id
        self.curr_id+=1
        return ret


