class Table():
    def __init__(self,table:dict,prog_id:int):
        self.table_id = str(table["table_id"])
        self.capacity = table["capacity"]
        self.head_seats = table.get("head_seats", 0)
        self.model_id = prog_id

class Reservation():          
    def __init__(self,reservation:dict,prog_id:int):
          self.name = str(reservation["name"])
          self.size = reservation["size"]
          self.require_head = reservation.get("required_head",0)
          self.model_id = prog_id

    def get_name(self):
        return self.name
    def get_size(self):
        return self.size
    def get_require_head(self):
        return self.require_head
    def get_model_id(self):
        return self.model_id

class Aggregate_reservation():
    def __init__(self,reservations:list[Reservation],prog_id:int):
        self.reservations = reservations
        self.name = "+".join([res.get_name() for res in reservations])
        self.size = sum([res.size for res in reservations])
        self.require_head = any([res.require_head for res in reservations]) #TODO deal with both head required
        self.model_id = prog_id

class Prog_id_gen():
    def __init__(self):
        self.curr_id = 0
    def get_next(self):
        ret = self.curr_id
        self.curr_id+=1
        return ret


