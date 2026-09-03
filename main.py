from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

class ProductoCreate(BaseModel):
    nombre: str
    stock: int = 0
    precio_1: float = 0.0
    precio_2: float = 0.0
    precio_3: float = 0.0
    precio_4: float = 0.0

class StockUpdate(BaseModel):
    stock: int

class EstadoUpdate(BaseModel):
    estado: str

class PedidoCreate(BaseModel):
    cliente_nombre: str
    detalle: str
    lista_precio: str
    estado: str = "Pendiente"

@app.get("/api/productos")
def listar_productos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM productos ORDER BY id ASC")
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return productos

@app.post("/api/productos")
def crear_producto(prod: ProductoCreate):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO productos (nombre, stock, precio_1, precio_2, precio_3, precio_4) 
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (prod.nombre, prod.stock, prod.precio_1, prod.precio_2, prod.precio_3, prod.precio_4)
        )
        nuevo_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()
        return {"id": nuevo_id, "mensaje": "Producto creado con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/productos/{producto_id}/stock")
def actualizar_stock(producto_id: int, stock_data: StockUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE productos SET stock = %s WHERE id = %s",
        (stock_data.stock, producto_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"mensaje": "Stock actualizado"}

@app.get("/api/pedidos")
def listar_pedidos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pedidos.*, COALESCE(clientes.nombre, pedidos.cliente_nombre, 'Cliente General') AS cliente 
        FROM pedidos 
        LEFT JOIN clientes ON pedidos.cliente_id = clientes.id 
        ORDER BY pedidos.id DESC
    """)
    pedidos = cur.fetchall()
    cur.close()
    conn.close()
    return pedidos

@app.post("/api/pedidos")
def crear_pedido(pedido: PedidoCreate):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO pedidos (cliente_nombre, detalle, lista_precio, estado) 
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (pedido.cliente_nombre, pedido.detalle, str(pedido.lista_precio), pedido.estado)
        )
        nuevo_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()
        return {"id": nuevo_id, "mensaje": "Pedido creado con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/pedidos/{pedido_id}/estado")
def actualizar_estado_pedido(pedido_id: int, estado_data: EstadoUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE pedidos SET estado = %s WHERE id = %s",
        (estado_data.estado, pedido_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"mensaje": "Estado actualizado"}

@app.delete("/api/pedidos/{pedido_id}")
def eliminar_pedido(pedido_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"mensaje": "Pedido eliminado"}

app.mount("/", StaticFiles(directory=".", html=True), name="static")
