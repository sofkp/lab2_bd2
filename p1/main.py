import struct
import os

class Record:
    def __init__(self, id=-1, name="", cant=-1, price=-1, date="", deleted=False, next=-1, aux=False):
        self.id = id
        self.name = name
        self.cant = cant
        self.price = price
        self.date = date
        self.next = next
        self.deleted = deleted
        self.aux = aux

    def __str__(self):
        return f'{self.id} | {self.name} | {self.cant} | {self.price} | {self.date} | next: {self.next} | aux: {self.aux}'

    def key(self):
        return self.id

    def is_deleted(self):
        return self.deleted

    def is_smaller(self, val):
        return self.key() <= val

    def to_binary(self):
        format_str = 'i30sif10si??'
        return struct.pack(format_str,
                           self.id,
                           self.name.encode().ljust(30, b'\x00'),
                           self.cant,
                           self.price,
                           self.date.encode().ljust(10, b'\x00'),
                           self.next,
                           self.deleted,
                           self.aux)

    @staticmethod
    def from_binary(data):
        id, name, cant, price, date, next, deleted, aux = struct.unpack('i30sif10si??', data)
        return Record(id, name.decode().strip(), cant, price, date.decode().strip(), deleted, next, aux)

class Sequential:
    def __init__(self, filename):
        self.filename = filename
        self.aux_filename = "aux.bin"
        self.HEADER_SIZE = 5

        if not os.path.exists(self.filename):
            with open(self.filename, 'wb') as f:
                f.write(struct.pack("i?", -1, False))

        self.RECORD_SIZE = struct.calcsize('i30sif10si??')
        print(f"Tamaño de registro calculado: {self.RECORD_SIZE} bytes")

    def write_start(self, start_pos, aux):
        with open(self.filename, 'r+b') as f:
            f.write(struct.pack("i?", start_pos, aux))

    def get_start(self):
        with open(self.filename, 'rb') as f:
            data = f.read(5)
            if len(data) < 5:
                return -1, False
            return struct.unpack("i?", data)

    def get_record_at(self, aux, pos):
        filename = self.aux_filename if aux else self.filename
        try:
            with open(filename, "rb") as f:
                offset = self.HEADER_SIZE + pos * self.RECORD_SIZE if not aux else pos * self.RECORD_SIZE
                f.seek(offset)
                data = f.read(self.RECORD_SIZE)
                if len(data) < self.RECORD_SIZE:
                    return None
                return Record.from_binary(data)
        except FileNotFoundError:
            return None

    def write_record_end(self, aux, record):
        filename = self.aux_filename if aux else self.filename
        with open(filename, "ab") as f:
            pos = (f.tell() - (5 if not aux else 0)) // self.RECORD_SIZE
            f.write(record.to_binary())
            return pos

    def write_record_at(self, record, pos, aux):
        filename = self.aux_filename if aux else self.filename
        with open(filename, "r+b") as f:
            offset = 5 + pos * self.RECORD_SIZE if not aux else pos * self.RECORD_SIZE
            f.seek(offset)
            f.write(record.to_binary())

    def binary_search(self, key):
        with open(self.filename, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            if file_size <= self.HEADER_SIZE:
                return -1
            num_records = (file_size - self.HEADER_SIZE) // self.RECORD_SIZE

        left, right = 0, num_records - 1
        result = -1

        while left <= right:
            mid = (left + right) // 2
            record = self.get_record_at(False, mid)
            if record is None:
                break

            if record.key() < key:
                result = mid
                left = mid + 1
            else:
                right = mid - 1

        return result

    def print_all(self):
        print("\nContenido del archivo principal:")
        start_pos, start_aux = self.get_start()
        print(f"Encabezado (start position): {start_pos}{'a' if start_aux else 'd'}")

        with open(self.filename, "rb") as f:
            header = struct.unpack("i", f.read(4))[0]
            print(f"Encabezado (start position): {header}d" if header != -1 else "Encabezado (start position): -1")
            
            pos = 0
            while True:
                data = f.read(self.RECORD_SIZE)
                if not data or len(data) < self.RECORD_SIZE:
                    break
                record = Record.from_binary(data)
                if record:
                    next_str = "-1"
                    if record.next != -1:
                        next_str = f"{record.next}{'a' if record.aux else 'd'}"
                    print(f"Pos {pos}: {record} | → {next_str}")
                pos += 1

        print("\nContenido del archivo auxiliar:")
        try:
            with open(self.aux_filename, "rb") as f:
                pos = 0
                while True:
                    data = f.read(self.RECORD_SIZE)
                    if not data or len(data) < self.RECORD_SIZE:
                        break
                    record = Record.from_binary(data)
                    if record:
                        next_str = "-1"
                        if record.next != -1:
                            next_str = f"{record.next}{'a' if record.aux else 'd'}"
                        print(f"Pos {pos}: {record} | → {next_str}")
                    pos += 1
        except FileNotFoundError:
            print("No existe archivo auxiliar")


    def insert(self, record):
        with open(self.filename, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()

        if file_size <= self.HEADER_SIZE:
            self.write_start(0, False)
            self.write_record_at(record, 0, False)
            return

        pos = self.binary_search(record.key())
        start_pos, start_aux = self.get_start()

        if pos == -1:
            first_record = self.get_record_at(start_aux, start_pos)
            if first_record:
                new_pos = self.write_record_end(True, record)
                record.next = start_pos
                record.aux = start_aux
                self.write_record_at(record, new_pos, True)
                self.write_start(new_pos, True)
            return

        current = self.get_record_at(False, pos)
        if current is None:
            return

        if current.next == -1:
            if record.key() > current.key():
                new_pos = self.write_record_end(False, record)
                current.next = new_pos
                current.aux = False
                self.write_record_at(current, pos, False)
            return

        next_record = self.get_record_at(current.aux, current.next)
        if next_record and record.key() > current.key() and record.key() < next_record.key():
            record.next = current.next
            record.aux = current.aux
            new_pos = self.write_record_end(True, record)
            current.next = new_pos
            current.aux = True
            self.write_record_at(current, pos, False)
        else:
            prev_record = current
            prev_pos = pos
            prev_aux = False
            next_pos = current.next
            next_aux = current.aux

            while next_pos != -1:
                next_record = self.get_record_at(next_aux, next_pos)
                if not next_record or record.key() < next_record.key():
                    break
                prev_record = next_record
                prev_pos = next_pos
                prev_aux = next_aux
                next_pos = next_record.next
                next_aux = next_record.aux

            record.next = prev_record.next
            record.aux = prev_record.aux
            new_pos = self.write_record_end(True, record)
            prev_record.next = new_pos
            prev_record.aux = True
            self.write_record_at(prev_record, prev_pos, prev_aux)

    def search(self, key):
        pos = self.binary_search(key)
        if pos == -1:
            pos, aux = self.get_start()
            if pos == -1:
                return None
            record = self.get_record_at(aux, pos)
        else:
            record = self.get_record_at(False, pos)

        while record:
            if not record.deleted and record.id == key:
                return record
            if record.next == -1:
                break
            print(f"aux: {record.aux} and next: {record.next}")
            record = self.get_record_at(record.aux, record.next)

        return None

    def search_range(self, mini, maxi):
        results = []
        with open(self.filename, "rb") as f:
            f.seek(5)
            while True:
                data = f.read(self.RECORD_SIZE)
                if not data or len(data) < self.RECORD_SIZE:
                    break
                record = Record.from_binary(data)
                if not record or record.deleted:
                    continue
                if mini <= record.id <= maxi:
                    results.append(record)

                next_ptr = record.next
                while next_ptr != -1:
                    aux_record = self.get_record_at(True, next_ptr)
                    if aux_record and not aux_record.deleted and mini <= aux_record.id <= maxi:
                        results.append(aux_record)
                    if aux_record is None:
                        break
                    next_ptr = aux_record.next

        return results

    def delete(self, key):
        start_pos, aux = self.get_start()
        if start_pos == -1:
            return False

        prev_pos = -1
        prev_aux = False
        pos = start_pos

        while current_pos != -1:
            record = self.get_record_at(current_aux, current_pos)
            if not record:
                break

            if record.id == key and not record.deleted:
                record.deleted = True
                self.write_record_at(record, current_pos, current_aux)

                if prev_pos == -1:
                    self.write_start(record.next, record.aux)
                else:
                    prev_record = self.get_record_at(prev_aux, prev_pos)
                    prev_record.next = record.next
                    self.write_record_at(prev_record, prev_pos, prev_aux)
                else:
                    self.write_start(record.next, record.aux)
                return True

            prev_pos = current_pos
            prev_aux = current_aux
            current_pos = record.next
            current_aux = record.aux

        return False

def main():
    for fname in ["test.bin", "aux.bin"]:
        if os.path.exists(fname):
            os.remove(fname)

    file = Sequential("test.bin")

    records = [
        Record(4, "melanie", 30, 10.4, "2004-10-12"),
        Record(5, "melanie", 30, 10.4, "2004-10-12"),
        Record(2, "melanie", 30, 10.4, "2004-10-12"),
        Record(7, "melanie", 30, 10.4, "2004-10-12"),
        Record(8, "melanie", 30, 10.4, "2004-10-12"),
        Record(10, "melanie", 30, 10.4, "2004-10-12"),
        Record(20, "melanie", 30, 10.4, "2004-10-12"),
        Record(1, "melanie", 30, 10.4, "2004-10-12"),
        Record(6, "melanie", 30, 10.4, "2004-10-12")
    ]

    for record in records:
        print(f"\nInsertando registro con ID: {record.id}")
        file.insert(record)
        file.print_all()

    print("\nResultado final:")
    file.print_all()

    print("\nSEARCH:")
    print(file.search(8))
    print(file.search(2))

    print("\nsearch rango:")
    file.search_range(5, 10)

    print("\neliminar:")
    print(file.delete(8))
    print(file.delete(2))

    file.print_all()

if __name__ == "__main__":
    main()
