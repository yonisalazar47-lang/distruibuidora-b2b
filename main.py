from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
from init_db import init_db

# Crea las tablas al arrancar
init_db()

app = FastAPI()

class EstadoPedido(BaseModel):
    estado: str

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/productos")
def obtener_productos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return productos

@app.get("/api/pedidos")
def obtener_pedidos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pedidos ORDER BY id DESC")
    pedidos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return pedidos

@app.put("/api/pedidos/{pedido_id}/estado")
def actualizar_estado(pedido_id: int, estado_data: EstadoPedido):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (estado_data.estado, pedido_id))
    conn.commit()
    conn.close()
    return {"ok": True}

app.mount("/", StaticFiles(directory=".", html=True), name="static")