import struct
import os
import pandas as pd

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


class AVLTree:
    def __init__(self, filename):
        self.filename = filename
        root = -1
        with open(filename, "rb+") as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()

            if file_size != 0:
                f.seek(0)
                root = struct.unpack("i", f.read(4))[0]
            else:
                f.write(struct.pack("i", -1)) # root, size
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

    def _balance(self, node):
        if node is None:
            return node
        
        balance = self._get_balance(node)

        if balance > 1:
            if self._get_balance(node.left) < 0:
                node.left = self._left_rotate(node.left)
            return self._right_rotate(node)

        if balance < -1:
            if self._get_balance(node.right) > 0:
                node.right = self._right_rotate(node.right)
            return self._left_rotate(node)

        return node
    
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

    def _find(self, node, value):
        if not node:
            return False
        if node.data == value:
            return True
        elif value < node.data:
            return self._find(node.left, value)
        else:
            return self._find(node.right, value)

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
        self.root = self._remove(self.root, value)

    def _remove(self, node, value):
        if node is None:
            return node

        if value < node.data:
            node.left = self._remove(node.left, value)
        elif value > node.data:
            node.right = self._remove(node.right, value)
        else:
            # Caso 1: Nodo con solo un hijo o sin hijos
            if node.left is None and node.right is None:
                return None
            # Caso 2: Nodo con un hijo
            elif node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            # Caso 3: Nodo con dos hijos
            else:
                max_value = self._max_value(node.left)
                node.data = max_value
                node.left = self._remove(node.left, max_value)

        # Actualizamos la altura y balanceamos el nodo
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        return self._balance(node)

    def display_pretty(self):
        self.get_root()
        self._display_pretty(self.root, 1)

    def _display_pretty(self, node_pos, level):
        if node_pos != -1:
            node = self.get_node_at(node_pos)
            self._display_pretty(node.right, level + 1)
            print(" " * 4 * level + "->", node.key())
            self._display_pretty(node.left, level + 1)


def main():
    file = AVLTree("test.bin")

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

    # print(file.find(2))

    # print()
    # file.display_pretty()

    # print()

    # file.remove(2)
    # file.remove(4)
    # file.remove(5)

    # file.display_pretty()

    # print()

    file.load("sales_dataset.csv")

    print(file.get_preorder())


main()