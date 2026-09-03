from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
from init_db import init_db

# Crea e inicializa las tablas al arrancar
init_db()

app = FastAPI()

# Modelos de datos
class EstadoPedido(BaseModel):
    estado: str

class ProductoCreate(BaseModel):
    nombre: str
    stock: int
    precio_1: float
    precio_2: float
    precio_3: float
    precio_4: float

class PedidoCreate(BaseModel):
    cliente: str
    lista_precio: int
    detalle: str
    estado: str = "pendiente"

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- ENDPOINTS PRODUCTOS ---

@app.get("/api/productos")
def obtener_productos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return productos

@app.post("/api/productos")
def crear_producto(prod: ProductoCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO productos (nombre, stock, precio_1, precio_2, precio_3, precio_4)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (prod.nombre, prod.stock, prod.precio_1, prod.precio_2, prod.precio_3, prod.precio_4))
    conn.commit()
    conn.close()
    return {"ok": True}

# --- ENDPOINTS PEDIDOS ---

@app.get("/api/pedidos")
def obtener_pedidos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pedidos ORDER BY id DESC")
    pedidos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return pedidos

@app.post("/api/pedidos")
def crear_pedido(ped: PedidoCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pedidos (cliente, lista_precio, detalle, estado)
        VALUES (?, ?, ?, ?)
    ''', (ped.cliente, ped.lista_precio, ped.detalle, ped.estado))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.put("/api/pedidos/{pedido_id}/estado")
def actualizar_estado(pedido_id: int, estado_data: EstadoPedido):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (estado_data.estado, pedido_id))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.delete("/api/pedidos/{pedido_id}")
def eliminar_pedido(pedido_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

app.mount("/", StaticFiles(directory=".", html=True), name="static")
