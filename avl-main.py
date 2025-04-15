import struct
import os
import pandas as pd
import csv
import time
import matplotlib.pyplot as plt

RECORD_SIZE = struct.calcsize("i30sif10s")
NODE_SIZE = struct.calcsize("iii") + RECORD_SIZE

class Record:
        def __init__(self, id, name, cant, price, date):
            self.id = id # int
            self.name = name # 30s
            self.cant = cant # int
            self.price = price # float
            self.date = date # 10s

        def __str__(self):
            return f'{self.id} |  {self.name} | {self.cant} | {self.price} | {self.date}'

        def key(self):
            return self.id
        
        def to_binary(self):
            return struct.pack('i30sif10s', self.id, self.name.encode(), self.cant, self.price, self.date.encode())

        @staticmethod
        def from_binary(data):
            id, name, cant, price, date = struct.unpack('i30sif10s', data)
            return Record(id, name.decode().strip(), cant, price, date.decode().strip()) 
        
class Node:
    def __init__(self, record, height = 0, left = -1, right = -1):
        self.record = record
        self.height = height
        self.left = left
        self.right = right

    def __str__(self):
        return f'Record: {self.record} \n Left: {self.left} | Right: {self.right} | Height: {self.height}'

    def to_binary(self):
        header = struct.pack("iii", self.left, self.right, self.height)
        rec = self.record.to_binary()
        return header + rec
    
    @staticmethod
    def from_binary(data):
        left, right, height = struct.unpack("iii", data[:12])
        record = Record.from_binary(data[12:])
        return Node(record=record, left=left, right=right, height=height)
    
    def key(self):
        return self.record.id


import os
import struct

class AVLTree:
    def __init__(self, filename):
        self.filename = filename
        root = -1
        if not os.path.exists(filename):
            with open(filename, "wb") as f:
                f.write(struct.pack("i", -1))
            self.root = -1
        else:
            with open(filename, "rb+") as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()

                if file_size != 0:
                    f.seek(0)
                    root = struct.unpack("i", f.read(4))[0]
                else:
                    f.seek(0)
                    f.write(struct.pack("i", -1))
            self.root = root

    def get_node_at(self, pos):
        with open(self.filename, "rb+") as f:
            f.seek(pos * NODE_SIZE + 4)
            return Node.from_binary(f.read(NODE_SIZE))
    
    def write_node_at(self, node, pos):
        with open(self.filename, "rb+") as f:
            f.seek(0)
            f.seek(pos * NODE_SIZE + 4)
            f.write(node.to_binary())
    
    def get_root(self):
        with open(self.filename, "rb+") as f:
            f.seek(0)
            self.root = struct.unpack("i", f.read(4))[0]
    
    def write_root(self):
        with open(self.filename, "rb+") as f:
            f.seek(0)
            f.write(struct.pack("i", self.root))
    
    def load(self, file_csv):
        df = pd.read_csv(file_csv)

        for index, row in df.iterrows():
            record = Record(row.iloc[0], row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4])
            self.insert(record)
            print(f"inserted {record.key()}")

    def insert(self, record):
        self.get_root()
        self.root = self._insert(self.root, record)
        self.write_root()

    def _insert(self, node_pos, record):
        if node_pos == -1:
            with open(self.filename, "ab+") as f:
                pos = (f.tell() - 4) // NODE_SIZE  # Assuming 4 bytes for metadata or header
                self.write_node_at(Node(record), pos)
                return pos

        node = self.get_node_at(node_pos)
        if record.key() < node.key():
            node.left = self._insert(node.left, record)
        else:
            node.right = self._insert(node.right, record)

        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        self.write_node_at(node, node_pos)
        balance = self._get_balance(node_pos)
        # Rotations based on balance factor
        if balance > 1:  # Left heavy
            left_node = self.get_node_at(node.left)
            if record.key() < left_node.key():  # Left-Left case
                self.write_node_at(node, node_pos)
                return self._right_rotate(node_pos)
            else:  # Left-Right case
                node.left = self._left_rotate(node.left)
                self.write_node_at(node, node_pos)
                return self._right_rotate(node_pos)

        if balance < -1:  # Right heavy
            right_node = self.get_node_at(node.right)
            if record.key() > right_node.key():  # Right-Right case
                self.write_node_at(node, node_pos)
                return self._left_rotate(node_pos)
            else:  # Right-Left case
                node.right = self._right_rotate(node.right)
                self.write_node_at(node, node_pos)
                return self._left_rotate(node_pos)


        self.write_node_at(node, node_pos)
        return node_pos

    def _left_rotate(self, z_pos):
        z = self.get_node_at(z_pos)
        y_pos = z.right
        y = self.get_node_at(y_pos)
        T2 = y.left

        # Perform rotation
        y.left = z_pos  # z becomes the left child of y
        z.right = T2  # T2 becomes the right child of z

        # Update heights after the rotation
        z.height = 1 + max(self._get_height(z.left), self._get_height(z.right))
        self.write_node_at(z, z_pos)
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        # Write the nodes back to their positions in the file
        self.write_node_at(y, y_pos)

        return y_pos  # Return the new root of the subtree

    def _right_rotate(self, z_pos):
        z = self.get_node_at(z_pos)
        y_pos = z.left
        y = self.get_node_at(y_pos)
        T3 = y.right

        # Perform rotation
        y.right = z_pos  # z becomes the right child of y
        z.left = T3  # T3 becomes the left child of z
        # Update heights after the rotation
        z.height = 1 + max(self._get_height(z.left), self._get_height(z.right))
        self.write_node_at(z, z_pos)
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        # Write the nodes back to their positions in the file
        self.write_node_at(y, y_pos)
        self.write_node_at(z, z_pos)

        return y_pos  # Return the new root of the subtree
        
    def print_file(self):
        with open(self.filename, "ab+") as f:
            end = f.tell()
            i = 0
            while i * NODE_SIZE + 4 < end:
                data = self.get_node_at(i)
                print(data)
                i+=1

    def _balance(self, node_pos):
        if node_pos == -1:
            return node_pos

        balance = self._get_balance(node_pos)
        node = self.get_node_at(node_pos)

        if balance > 1:
            if self._get_balance(node.left) < 0:
                node.left = self._left_rotate(node.left)
                self.write_node_at(node, node_pos)
            return self._right_rotate(node_pos)

        if balance < -1:
            if self._get_balance(node.right) > 0:
                node.right = self._right_rotate(node.right)
                self.write_node_at(node, node_pos)
            return self._left_rotate(node_pos)

        self.write_node_at(node, node_pos)
        return node_pos
    
    def _get_height(self, node_pos):
        if node_pos != -1:
            node = self.get_node_at(node_pos)
            return node.height
        return -1

    def _get_balance(self, node_pos):
        node = self.get_node_at(node_pos)
        return self._get_height(node.left) - self._get_height(node.right)

    def find(self, value):
        return self._find(self.root, value)

    def _find(self, node_pos, value):
        if node_pos == -1:
            return None
        node = self.get_node_at(node_pos)
        if value == node.record.id:
            return node.record
        elif value < node.record.id:
            return self._find(node.left, value)
        else:
            return self._find(node.right, value)
        
    def search_rango(self, mini, maxi):
        self.get_root()
        result = []
        self._search_rango(self.root, mini, maxi, result)
        return result

    def _search_rango(self, node_pos, mini, maxi, result):
        if node_pos == -1:
            return
        node = self.get_node_at(node_pos)
        key = node.key()
        if mini < key:
            self._search_rango(node.left, mini, maxi, result)
        if mini <= key <= maxi:
            result.append(node.record)
        if key < maxi:
            self._search_rango(node.right, mini, maxi, result)

    def get_preorder(self):
        return self._get_preorder(self.root)

    def _get_preorder(self, node_pos):
        if node_pos == -1:
            return ""
        node = self.get_node_at(node_pos)
        return self._get_preorder(node.left) + str(node.record) + "\n" + self._get_preorder(node.right)

    def height(self):
        return self._get_height(self.root)

    def min_value(self):
        return self._min_value(self.root)

    def _min_value(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current.data if current else None

    def max_value(self):
        return self._max_value(self.root)

    def _max_value(self, node):
        current = node
        while current.right is not None:
            current = current.right
        return current.data if current else None
    
    def _max_node_pos(self, node_pos):
        current_pos = node_pos
        current = self.get_node_at(current_pos)
        while current.right != -1:
            current_pos = current.right
            current = self.get_node_at(current_pos)
        return current_pos

    def is_balanced(self):
        return self._is_balanced(self.root)

    def _is_balanced(self, node):
        if node is None:
            return True
        balance = self._get_balance(node)
        return abs(balance) <= 1 and self._is_balanced(node.left) and self._is_balanced(node.right)

    def size(self):
        return self._size(self.root)

    def _size(self, node):
        if node is None:
            return 0
        return 1 + self._size(node.left) + self._size(node.right)

    def remove(self, value):
        self.get_root()
        self.root = self._remove(self.root, value)
        self.write_root()


    def _remove(self, node_pos, value):
        if node_pos == -1:
            return -1

        node = self.get_node_at(node_pos)

        if value < node.key():
            node.left = self._remove(node.left, value)
        elif value > node.key():
            node.right = self._remove(node.right, value)
        else:
            # Caso 1: Nodo con solo un hijo o sin hijos
            if node.left == -1 and node.right == -1:
                return -1
            # Caso 2: Nodo con un hijo
            elif node.left == -1:
                return node.right
            elif node.right == -1:
                return node.left
            # Caso 3: Nodo con dos hijos
            else:
                max_node = self.get_node_at(self._max_node_pos(node.left))
                node.record = max_node.record
                node.left = self._remove(node.left, max_node.key())


        # Actualizamos la altura y balanceamos el nodo
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        self.write_node_at(node, node_pos)
        return self._balance(node_pos)


    def display_pretty(self):
        self.get_root()
        self._display_pretty(self.root, 1)

    def _display_pretty(self, node_pos, level):
        if node_pos != -1:
            node = self.get_node_at(node_pos)
            self._display_pretty(node.right, level + 1)
            print(" " * 4 * level + "->", node.key())
            self._display_pretty(node.left, level + 1)

def medir_tiempos_por_cantidad(avl, rows, cantidades):
    tiempos_insert = []
    tiempos_busqueda = []
    tiempos_rango = []
    tiempos_delete = []

    for n in cantidades:
        sample = rows[:n]

        if os.path.exists("avl.dat"):
            os.remove("avl.dat")
        avl = AVLTree("avl.dat")

        t1 = time.time()
        for row in sample:
            id = int(row[0])
            nombre = row[1]
            cantidad = int(row[2])
            precio = float(row[3])
            fecha = row[4]
            avl.insert(Record(id, nombre, cantidad, precio, fecha))
        t2 = time.time()
        tiempos_insert.append(t2 - t1)

        t1 = time.time()
        for i in range(1, n + 1, max(1, n // 10)):
            avl.find(i)
        t2 = time.time()
        tiempos_busqueda.append(t2 - t1)

        t1 = time.time()
        avl.search_rango(1, n)
        t2 = time.time()
        tiempos_rango.append(t2 - t1)

        t1 = time.time()
        for i in range(1, n + 1, max(1, n // 10)):
            avl.remove(i)
        t2 = time.time()
        tiempos_delete.append(t2 - t1)

    return tiempos_insert, tiempos_busqueda, tiempos_rango, tiempos_delete

def graficar_lineal(cantidades, tiempos, titulo, nombre_archivo):
    plt.figure(figsize=(10, 6))
    plt.plot(cantidades, tiempos, marker='o', linestyle='-', linewidth=2.5, color='#5F9EA0', label=titulo)
    for i, tiempo in enumerate(tiempos):
        plt.text(cantidades[i], tiempo, f"{tiempo:.4f}s", ha='center', va='bottom', fontsize=9)
    plt.title(f"{titulo} vs Cantidad de registros", fontsize=14)
    plt.xlabel("Cantidad de registros")
    plt.ylabel("Tiempo (segundos)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(nombre_archivo)
    plt.show()

def main():
    cantidades = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    with open("sales_dataset.csv", newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        rows = list(reader)

    avl = AVLTree("avl.dat")
    tiempos_insert, tiempos_busqueda, tiempos_rango, tiempos_delete = medir_tiempos_por_cantidad(avl, rows, cantidades)

    graficar_lineal(cantidades, tiempos_insert, "Tiempo de Inserción", "grafico_insercion.png")
    graficar_lineal(cantidades, tiempos_busqueda, "Tiempo de Búsqueda", "grafico_busqueda.png")
    graficar_lineal(cantidades, tiempos_rango, "Tiempo de Búsqueda por Rango", "grafico_rango.png")
    graficar_lineal(cantidades, tiempos_delete, "Tiempo de Eliminación", "grafico_eliminacion.png")


'''def main():
    avl = AVLTree("avl.dat")

    with open("sales_dataset.csv", newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            id = int(row[0])
            nombre = row[1]
            cantidad = int(row[2])
            precio = float(row[3])
            fecha = row[4]
            avl.insert(Record(id, nombre, cantidad, precio, fecha))

    #avl.display_pretty()

    # r1 = Record(4, "melanie", 30, 10.4, "2004-10-12")
    # r2 = Record(5, "melanie", 30, 10.4, "2004-10-12")
    # r3 = Record(2, "melanie", 30, 10.4, "2004-10-12")
    # r4 = Record(7, "melanie", 30, 10.4, "2004-10-12")
    # r5 = Record(8, "melanie", 30, 10.4, "2004-10-12")
    # r6 = Record(10, "melanie", 30, 10.4, "2004-10-12")
    # r7 = Record(20, "melanie", 30, 10.4, "2004-10-12")

    # # file.insert(r1)
    # # file.insert(r2)
    # # file.insert(r3)
    # # file.insert(r4)
    # # file.insert(r5)
    # # file.insert(r6)
    # # file.display_pretty()

    # # file.insert(r7)
    # # file.display_pretty()

    # r8 = Record(112, "melanie", 30, 10.4, "2004-10-12")
    # r9 = Record(1, "melanie", 30, 10.4, "2004-10-12")

    # file.insert(r8)
    # file.display_pretty()
    # print()
    # file.insert(r9)
    # file.display_pretty()

    # print()

    print(avl.find(2))

    records = avl.search_rango(5, 15)
    for record in records:
        print(record)


    # print()
    # file.display_pretty()

    # print()

    avl.remove(2)
    avl.remove(4)
    avl.remove(5)

    print(avl.find(2))
    print(avl.find(4))
    print(avl.find(5))

    avl.display_pretty()

    # file.display_pretty()

    # print()

    #print(avl.get_preorder())

'''
main()
