from Optimizer.mnemonics import *


def _normalize_capacities(capacities) -> list[int]:
    if isinstance(capacities, int):
        capacities = [capacities]
    return [int(c) for c in capacities if int(c) > 0]


def _compute_split_sizes(total_size: int, capacities) -> list[int]:
    capacities = _normalize_capacities(capacities)
    if not capacities or total_size <= 0:
        return []

    sizes: list[int] = []
    used_caps: list[int] = []
    remaining = int(total_size)
    idx = 0
    while remaining > 0:
        cap = capacities[idx] if idx < len(capacities) else capacities[-1]
        if cap <= 0:
            break
        take = cap if remaining > cap else remaining
        sizes.append(take)
        used_caps.append(cap)
        remaining -= take
        idx += 1

    if len(sizes) >= 2 and sizes[-1] < 6:
        total_last_two = sizes[-2] + sizes[-1]
        prev_cap = used_caps[-2]
        last_cap = used_caps[-1]
        min_last = max(1, total_last_two - prev_cap)
        max_last = min(last_cap, total_last_two - 1)
        if min_last <= max_last:
            target_last = (total_last_two + 1) // 2
            if target_last < min_last:
                target_last = min_last
            elif target_last > max_last:
                target_last = max_last
            sizes[-1] = target_last
            sizes[-2] = total_last_two - target_last

    return sizes

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
    
    def split(self,capacities:list[int])->list['Reservation']:
        """
        Split a reservation into parts using the provided capacities in order.
        If the last part is smaller than 6, rebalance it with the previous part
        while respecting both capacities.
        """
        capacities = _normalize_capacities(capacities)
        sizes = _compute_split_sizes(self.size, capacities)
        if not sizes:
            return []

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
        self.show_name = "+".join([res.show_name for res in reservations])
        self.reservation_dicts = [res.get_dict() for res in reservations]

    #@override
    def split(self, capacities): #TODO check
        """
        Split an aggregate reservation using the provided capacities in order.
        Sub-reservations are only split when necessary to hit the target sizes.
        """
        capacities = _normalize_capacities(capacities)
        if not capacities or len(self.reservations) == 0:
            return []

        if len(self.reservations) == 1:
            child = self.reservations[0]
            return child.split(capacities)

        target_sizes = _compute_split_sizes(self.size, capacities)
        if not target_sizes:
            return []

        def split_reservation_by_sizes(res: Reservation, sizes: list[int]) -> list[Reservation]:
            parts: list[Reservation] = []
            for i, s in enumerate(sizes, start=1):
                new_dict = res.original_dict.copy()
                new_dict[RESERVATION_SIZE_ATTR] = s
                new_dict[RESERVATION_REQUIRE_HEAD_ATTR] = res.get_require_head() if i == 1 else 0
                try:
                    base_name = str(new_dict.get(RESERVATION_NAME_ATTR, res.get_name()))
                except Exception:
                    base_name = res.get_name()
                new_dict[RESERVATION_NAME_ATTR] = f"{base_name}-part{i}"
                parts.append(Reservation(new_dict, prog_id=res.get_model_id()))
            return parts

        groups: list[list[Reservation]] = []
        current_group: list[Reservation] = []
        current_size = 0
        target_idx = 0

        for res in self.reservations:
            item = res
            while True:
                if target_idx >= len(target_sizes):
                    if current_group:
                        current_group.append(item)
                        groups.append(current_group)
                    else:
                        groups.append([item])
                    current_group = []
                    current_size = 0
                    break

                target = target_sizes[target_idx]
                remaining = target - current_size
                if remaining <= 0:
                    if current_group:
                        groups.append(current_group)
                    current_group = []
                    current_size = 0
                    target_idx += 1
                    continue

                if item.get_size() <= remaining:
                    current_group.append(item)
                    current_size += item.get_size()
                    break

                first_size = remaining
                rest_size = item.get_size() - remaining
                parts = split_reservation_by_sizes(item, [first_size, rest_size])
                current_group.append(parts[0])
                current_size += parts[0].get_size()
                groups.append(current_group)
                current_group = []
                current_size = 0
                target_idx += 1
                item = parts[1]

        if current_group:
            groups.append(current_group)

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


