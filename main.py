from cmath import log
import struct

RECORD_SIZE = struct.calcsize("i30sif10si?")
k = log(1000)

class Record:
        def __init__(self, id, name, cant, price, date, deleted=False, next=-1, aux=False):
            self.id = id # int
            self.name = name # 30s
            self.cant = cant # int
            self.price = price # float
            self.date = date # 10s
            self.next = next # int
            self.deleted = deleted # int if 1 then deleted
            self.aux = aux

        def __str__(self):
            return f'{self.id} |  {self.name} | {self.cant} | {self.price} | {self.date}'

        def key(self):
            return self.id
        
        def is_deleted(self):
            return self.deleted
        
        def to_binary(self):
            return struct.pack('i30sif10si??', self.id, self.name.encode(), self.cant, self.price, self.date.encode(), self.next, self.deleted, self.aux)

        @staticmethod
        def from_binary(data):
            id, name, cant, price, date, next, deleted = struct.unpack('i30sif10si??', data)
            return Record(id, name.decode().strip(), cant, price, date.decode().strip(), deleted, next) 
        
class Sequential:
    def __init__(self, filename):
        self.filename = filename
        self.aux = "aux.bin"
        with open(self.filename, "ab+") as f:
            if f.tell() == 0:
                self.write_start(-1)
    
    def write_start(self, s):
        with open(self.filename, "wb+") as f:
            f.seek(0)
            f.write(struct.pack("i", s))
    
    def get_start(self):
        with open(self.filename, "wb+") as f:
            f.seek(0)
            return struct.unpack("i", f.read(4))
    
    def get_record_at(self, pos):
        with open(self.filename, "rb+") as f:
            f.seek(pos * RECORD_SIZE + 4)
            return Record.from_binary(f.read(RECORD_SIZE))
    
    def write_record_at(self, record, pos):
        with open(self.filename, "rb+") as f:
            f.seek(0)
            f.seek(pos * RECORD_SIZE + 4)
            f.write(record.to_binary())
    
    def binary(self, key):
        left, right = 0, 0
        result = -1
        with open(self.filename, "ab+") as f:
            right = f.tell() // RECORD_SIZE
        while left <= right:
            middle = (left+right) // 2
            record = self.get_record_at(middle)
            if record.key() <= key:  
                result = middle
                left = middle + 1 
            else:
                right = middle - 1
        return result

    def insert(self, record):
        replace_pos = self.binary(record.key())
        place = self.get_record_at(replace_pos)

        if place.is_deleted():
            if place.next == -1:
                # write record in replace_pos
            else:
                # find smaller in auxiliar space
                # write smaller in replace_pos
                # call delete on 
            next_pointer = place.next
            record.next = next_pointer
            return
        

        return
    
def main():
    return
main()

    
