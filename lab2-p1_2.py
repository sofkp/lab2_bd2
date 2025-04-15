import struct
import os
import csv
import random
import time
import matplotlib.pyplot as plt

class Venta:
    def __init__(self, id, nombre, cantidad, precio, fecha, izq=-1, der=-1):
        self.id = id
        self.nombre = nombre
        self.cantidad = cantidad
        self.precio = precio
        self.fecha = fecha
        self.izq = izq
        self.der = der

    def get(self):
        print(self.id, end='|')
        print(self.nombre, end='|')
        print(self.cantidad, end='|')
        print(f"{self.precio:.2f}", end='|')
        print(self.fecha)

FORMAT = "i30sif10sii"
RECORD_SIZE = struct.calcsize(FORMAT)

class BST_File:
    def __init__(self, BST_Filename):
        self.BST_Filename = BST_Filename
        if not os.path.exists(self.BST_Filename):
            with open(self.BST_Filename, "wb") as f:
                pass

    def insert(self, registro):
        with open(self.BST_Filename, "rb+") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                to_write = struct.pack( FORMAT,registro.id,registro.nombre.encode().ljust(30, b'\x00'),
                        registro.cantidad,registro.precio, registro.fecha.encode().ljust(10, b'\x00'),-1,-1)
                f.write(to_write)
                return
        self.insert_pos(registro, 0)

    def insert_pos(self, registro, pos):
        with open(self.BST_Filename, "rb+") as f:
            while True:
                f.seek(pos * RECORD_SIZE)
                data = f.read(RECORD_SIZE)
                pid, pnombre, pcantidad, pprecio, pfecha, pizq, pder = struct.unpack(FORMAT, data)

                if registro.id < pid:
                    if pizq != -1:
                        pos = pizq
                    else:
                        f.seek(0, os.SEEK_END)
                        new_pos = f.tell() // RECORD_SIZE
                        to_write = struct.pack( FORMAT,registro.id,registro.nombre.encode().ljust(30, b'\x00'),
                            registro.cantidad,registro.precio, registro.fecha.encode().ljust(10, b'\x00'),-1,-1)
                        f.write(to_write)
                        pizq = new_pos
                        f.seek(pos * RECORD_SIZE)
                        f.write(struct.pack(FORMAT, pid, pnombre, pcantidad, pprecio, pfecha, pizq, pder))
                        break
                elif registro.id > pid:
                    if pder != -1:
                        pos = pder
                    else:
                        f.seek(0, os.SEEK_END)
                        new_pos = f.tell() // RECORD_SIZE
                        to_write = struct.pack( FORMAT,registro.id,registro.nombre.encode().ljust(30, b'\x00'),
                            registro.cantidad,registro.precio, registro.fecha.encode().ljust(10, b'\x00'),-1,-1)
                        f.write(to_write)
                        pder = new_pos
                        f.seek(pos * RECORD_SIZE)
                        f.write(struct.pack(FORMAT, pid, pnombre, pcantidad, pprecio, pfecha, pizq, pder))
                        break
                else:
                    break 

    def search(self, key):
        return self.search_pos(key, 0)

    def search_pos(self, key, pos):
        with open(self.BST_Filename, "rb") as f:
            f.seek(pos * RECORD_SIZE)
            data = f.read(RECORD_SIZE)
            if not data:
                return None
            id, nombre, cantidad, precio, fecha, izq, der = struct.unpack(FORMAT, data)
            if key == id:
                return Venta(id, nombre.decode().strip('\x00'), cantidad, precio, fecha.decode().strip('\x00'), izq, der)
            elif key < id and izq != -1:
                return self.search_pos(key, izq)
            elif key > id and der != -1:
                return self.search_pos(key, der)
            return None

    def delete(self, key):
        with open(self.BST_Filename, "rb+") as f:
            while True:
                pos = f.tell()
                data = f.read(RECORD_SIZE)
                if not data:
                    break
                id, nombre, cantidad, precio, fecha, izq, der = struct.unpack(FORMAT, data)
                if id == key:
                    f.seek(pos)
                    to_write = struct.pack(FORMAT, -1, nombre, cantidad, precio, fecha, izq, der)
                    f.write(to_write)
                    return

    def search_rango(self, minimo, maximo):
        resultados = []
        with open(self.BST_Filename, "rb") as f:
            while True:
                data = f.read(RECORD_SIZE)
                if not data:
                    break
                id, nombre, cantidad, precio, fecha, izq, der = struct.unpack(FORMAT, data)
                if id == -1:
                    continue
                if minimo <= id <= maximo:
                    resultados.append(Venta(id, nombre.decode().strip('\x00'), cantidad, precio, fecha.decode().strip('\x00')))
        return resultados

    def print_file(self):
        with open(self.BST_Filename, "rb") as f:
            index = 0
            while True:
                data = f.read(RECORD_SIZE)
                if not data:
                    break
                id, nombre, cantidad, precio, fecha, izq, der = struct.unpack(FORMAT, data)
                if id == -1:
                    continue
                venta = Venta(id, nombre.decode().strip('\x00'), cantidad, precio, fecha.decode().strip('\x00'), izq, der)
                print(f"[{index}] ", end='')
                venta.get()
                index += 1

def medir_tiempos_por_cantidad(bst, rows, cantidades):
    tiempos_insert = []
    tiempos_busqueda = []
    tiempos_rango = []
    tiempos_delete = []

    for n in cantidades:
        sample = rows[:n]

        if os.path.exists("lab2_p2.dat"):
            os.remove("lab2_p2.dat")
        bst = BST_File("lab2_p2.dat")

        t1 = time.time()
        for row in sample:
            id = int(row[0])
            nombre = row[1]
            cantidad = int(row[2])
            precio = float(row[3])
            fecha = row[4]
            bst.insert(Venta(id, nombre, cantidad, precio, fecha))
        t2 = time.time()
        tiempos_insert.append(t2 - t1)

        t1 = time.time()
        for i in range(1, n + 1, max(1, n // 10)):
            bst.search(i)
        t2 = time.time()
        tiempos_busqueda.append(t2 - t1)

        t1 = time.time()
        bst.search_rango(1, n)
        t2 = time.time()
        tiempos_rango.append(t2 - t1)

        t1 = time.time()
        for i in range(1, n + 1, max(1, n // 10)):
            bst.delete(i)
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
    cantidades = [100, 200, 400, 600, 800, 1000]
    with open("sales_dataset.csv", newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        rows = list(reader)
        random.shuffle(rows)

    bst = BST_File("lab2_p2.dat")
    tiempos_insert, tiempos_busqueda, tiempos_rango, tiempos_delete = medir_tiempos_por_cantidad(bst, rows, cantidades)

    graficar_lineal(cantidades, tiempos_insert, "Tiempo de Inserción", "grafico_insercion.png")
    graficar_lineal(cantidades, tiempos_busqueda, "Tiempo de Búsqueda", "grafico_busqueda.png")
    graficar_lineal(cantidades, tiempos_rango, "Tiempo de Búsqueda por Rango", "grafico_rango.png")
    graficar_lineal(cantidades, tiempos_delete, "Tiempo de Eliminación", "grafico_eliminacion.png")


if __name__ == "__main__":
    main()
