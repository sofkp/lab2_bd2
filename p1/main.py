import struct
import os

import struct

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
        return f'{self.id} | {self.name} | {self.cant} | {self.price} | {self.date}'

    def key(self):
        return self.id

    def is_deleted(self):
        return self.deleted

    def is_smaller(self, val):
        return self.key() < val

    def to_binary(self):
        # Calcular el tamaño real del formato
        format_str = 'i30sif10si??'
        packed = struct.pack(format_str, 
                           self.id,
                           self.name.encode().ljust(30, b'\x00'),
                           self.cant, 
                           self.price,
                           self.date.encode().ljust(10, b'\x00'),
                           self.next, 
                           self.deleted,
                           self.aux)
        return packed

    @staticmethod
    def from_binary(data):
        try:
            id, name, cant, price, date, next, deleted, aux = struct.unpack('i30sif10si??', data)
            return Record(id, name.decode().strip(), cant, price, date.decode().strip(), deleted, next, aux)
        except struct.error as e:
            print(f"Error al desempaquetar: {e}")
            print(f"Datos recibidos: {data}, longitud: {len(data)}")
            return None

class Sequential:
    def __init__(self, filename):
        self.filename = filename
        self.aux_filename = "aux.dat"
        
        # Inicializar archivo principal con encabezado si está vacío
        if not os.path.exists(self.filename):
            with open(self.filename, 'wb') as f:
                f.write(struct.pack("i", -1))  # Encabezado inicial
        
        # Calcular RECORD_SIZE de manera precisa
        dummy_record = Record()
        self.RECORD_SIZE = len(dummy_record.to_binary())
        print(f"Tamaño de registro calculado: {self.RECORD_SIZE} bytes")

    def write_start(self, start_pos):
        with open(self.filename, 'r+b') as f:
            f.write(struct.pack("i", start_pos))

    def get_start(self):
        with open(self.filename, 'rb') as f:
            return struct.unpack("i", f.read(4))[0]

    def get_record_at(self, aux, pos):
        filename = self.aux_filename if aux else self.filename
        try:
            with open(filename, "rb") as f:
                f.seek(4+ pos * self.RECORD_SIZE)  # Saltar encabezado en archivo principal
                data = f.read(self.RECORD_SIZE)
                if len(data) != self.RECORD_SIZE:
                    print(f"Error: se esperaban {self.RECORD_SIZE} bytes, se obtuvieron {len(data)}")
                    return None
                return Record.from_binary(data)
        except FileNotFoundError:
            return None

    def write_record_end(self, aux, record):
        filename = self.aux_filename if aux else self.filename
        with open(filename, "ab") as f:
            pos = (f.tell() - (4 if not aux else 0)) // self.RECORD_SIZE
            f.write(record.to_binary())
            return pos

    def write_record_at(self, record, pos, aux):
        filename = self.aux_filename if aux else self.filename
        with open(filename, "r+b") as f:
            offset = 4 + pos * self.RECORD_SIZE if not aux else pos * self.RECORD_SIZE
            f.seek(offset)
            f.write(record.to_binary())

    def binary_search(self, key):
        # Obtener número de registros en archivo principal
        with open(self.filename, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            num_records = (file_size - 4) // self.RECORD_SIZE

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
        with open(self.filename, "rb") as f:
            header = struct.unpack("i", f.read(4))[0]
            print(f"Encabezado (start position): {header}")
            
            pos = 0
            while True:
                data = f.read(self.RECORD_SIZE)
                if not data or len(data) < self.RECORD_SIZE:
                    break
                record = Record.from_binary(data)
                if record:
                    print(f"Pos {pos}: {record}")
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
                        print(f"Pos {pos}: {record}")
                    pos += 1
        except FileNotFoundError:
            print("No existe archivo auxiliar")

    def insert(self, record):
        # Verificar si el archivo principal está vacío (solo tiene el encabezado)
        with open(self.filename, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()

        if file_size <= 4:  # Solo tiene el encabezado
            self.write_start(0)  # El primer registro está en posición 0
            self.write_record_at(record, 0, False)
            return

        # Buscar posición de inserción
        pos = self.binary_search(record.key())
        
        if pos == -1:  # Insertar al inicio
            old_start = self.get_start()
            record.next = old_start
            record.aux = False
            new_pos = self.write_record_end(False, record)
            self.write_start(new_pos)
            return

        # Obtener el registro en la posición encontrada
        current = self.get_record_at(False, pos)
        if current is None:
            return

        if current.next == -1:  # No hay siguiente, insertar al final
            new_pos = self.write_record_end(False, record)
            current.next = new_pos
            current.aux = False
            self.write_record_at(current, pos, False)
            return

        # Insertar en medio de la cadena
        record.next = current.next
        record.aux = current.aux
        new_pos = self.write_record_end(True, record)
        current.next = new_pos
        current.aux = True
        self.write_record_at(current, pos, False)


        def search(self, key):
            pos = self.binary_search(key)
            if pos == -1:
                pos = self.get_start()
                if pos == -1:
                    return None
                record = self.get_record_at(False, pos)
            else:
                record = self.get_record_at(False, pos)

            while record:
                if not record.deleted and record.id == key:
                    return record
                if record.next == -1:
                    break
                record = self.get_record_at(record.aux, record.next)

            return None

    def search(self, key):
        pos = self.binary_search(key)
        if pos == -1:
            pos = self.get_start()
            if pos == -1:
                return None
            record = self.get_record_at(False, pos)
        else:
            record = self.get_record_at(False, pos)

        while record:
            if not record.deleted and record.id == key:
                return record
            if record.next == -1:
                break
            record = self.get_record_at(record.aux, record.next)

        return None

    def search_range(self, mini, maxi):
        results = []
        with open(self.filename, "rb") as f:
            f.seek(4)
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
        start_pos = self.get_start()
        if start_pos == -1:
            return False

        prev_pos = -1
        prev_aux = False
        pos = start_pos
        aux = False

        while pos != -1:
            record = self.get_record_at(aux, pos)
            if not record:
                break

            if record.id == key and not record.deleted:
                record.deleted = True
                self.write_record_at(record, pos, aux)
                if prev_pos != -1:
                    prev_record = self.get_record_at(prev_aux, prev_pos)
                    prev_record.next = record.next
                    self.write_record_at(prev_record, prev_pos, prev_aux)
                else:
                    # es el primer registro
                    self.write_start(record.next)
                return True

            prev_pos = pos
            prev_aux = aux
            pos = record.next
            aux = record.aux

        return False



def main():
    # Limpiar archivos anteriores (para pruebas)
    for fname in ["test.dat", "aux.dat"]:
        if os.path.exists(fname):
            os.remove(fname)

    file = Sequential("test.dat")
    
    records = [
        Record(4, "melanie", 30, 10.4, "2004-10-12"),
        Record(5, "melanie", 30, 10.4, "2004-10-12"),
        Record(2, "melanie", 30, 10.4, "2004-10-12"),
        Record(7, "melanie", 30, 10.4, "2004-10-12"),
        Record(8, "melanie", 30, 10.4, "2004-10-12"),
        Record(10, "melanie", 30, 10.4, "2004-10-12"),
        Record(20, "melanie", 30, 10.4, "2004-10-12")
    ]
    
    for record in records:
        print(f"\nInsertando registro con ID: {record.id}")
        file.insert(record)
        file.print_all()
    
    print("\nResultado final:")
    file.print_all()

    print("\nSEARCH:")
    file.search(8)
    file.search(2)

    print("\nsearch rango:")
    file.search_range(5,10)

    print("\neliminar:")
    file.delete(8)
    file.delete(2)

if __name__ == "__main__":
    main()