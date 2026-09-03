from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import psycopg2
import psycopg2.extras
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tabla de productos si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL,
            precio_1 REAL NOT NULL DEFAULT 0,
            precio_2 REAL NOT NULL DEFAULT 0,
            precio_3 REAL NOT NULL DEFAULT 0,
            precio_4 REAL NOT NULL DEFAULT 0
        )
    """)
    
    # Asegurar columnas de precios por si la tabla ya existía
    for col in ["precio_1", "precio_2", "precio_3", "precio_4"]:
        cursor.execute(f"""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='productos' AND column_name='{col}') THEN
                    ALTER TABLE productos ADD COLUMN {col} REAL NOT NULL DEFAULT 0;
                END IF;
            END $$;
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id SERIAL PRIMARY KEY,
            cliente_nombre TEXT NOT NULL,
            lista_precio TEXT DEFAULT '1',
            detalle TEXT,
            estado TEXT DEFAULT 'pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("SELECT COUNT(*) as total FROM productos")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("INSERT INTO productos (nombre, stock, precio_1, precio_2, precio_3, precio_4) VALUES ('Harina 1kg', 100, 1000.0, 800.0, 700.0, 600.0)")
        cursor.execute("INSERT INTO productos (nombre, stock, precio_1, precio_2, precio_3, precio_4) VALUES ('COCA COLA 2LT', 1000, 3500.0, 3300.0, 3200.0, 3100.0)")
        cursor.execute("INSERT INTO productos (nombre, stock, precio_1, precio_2, precio_3, precio_4) VALUES ('SPRITE 2.25 LT', 1000, 3500.0, 3300.0, 3200.0, 3100.0)")
    
    conn.commit()
    cursor.close()
    conn.close()

@app.get("/", response_class=HTMLResponse)
def leer_raiz():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "Bienvenido a Distribuidora Don Vitorio."

@app.get("/index.html", response_class=HTMLResponse)
def leer_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin.html", response_class=HTMLResponse)
def leer_admin():
    with open("admin.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/productos")
def listar_productos(tipo_precio: str = "1"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, stock, precio_1, precio_2, precio_3, precio_4 FROM productos")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    lista_resultado = []
    for p in productos:
        if tipo_precio == "2":
            precio_final = p["precio_2"]
        elif tipo_precio == "3":
            precio_final = p["precio_3"]
        elif tipo_precio == "4":
            precio_final = p["precio_4"]
        else:
            precio_final = p["precio_1"]
            
        lista_resultado.append({
            "id": p["id"],
            "nombre": p["nombre"],
            "stock": p["stock"],
            "precio": precio_final
        })
        
    return lista_resultado

class ProductoNuevo(BaseModel):
    nombre: str
    stock: int
    precio_1: float
    precio_2: float
    precio_3: float
    precio_4: float

@app.post("/api/productos")
def crear_producto(p: ProductoNuevo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO productos (nombre, stock, precio_1, precio_2, precio_3, precio_4) VALUES (%s, %s, %s, %s, %s, %s)",
        (p.nombre, p.stock, p.precio_1, p.precio_2, p.precio_3, p.precio_4)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Producto creado con éxito"}

@app.get("/api/productos-admin")
def listar_productos_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, stock, precio_1, precio_2, precio_3, precio_4 FROM productos")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [
        {
            "id": p["id"],
            "nombre": p["nombre"],
            "stock": p["stock"],
            "precio_1": p["precio_1"],
            "precio_2": p["precio_2"],
            "precio_3": p["precio_3"],
            "precio_4": p["precio_4"]
        }
        for p in productos
    ]

class ItemPedido(BaseModel):
    producto_id: int
    cantidad: int

class PedidoEntrante(BaseModel):
    cliente_nombre: str
    lista_precio: Optional[str] = "1"
    items: List[ItemPedido]

@app.post("/api/pedidos")
def registrar_pedido(pedido: PedidoEntrante):
    if not pedido.cliente_nombre or not pedido.cliente_nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del comercio es obligatorio")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tipo_precio = str(pedido.lista_precio) if str(pedido.lista_precio) in ["1", "2", "3", "4"] else "1"
    
    detalle_items = []
    total_pedido = 0.0
    
    try:
        for item in pedido.items:
            precio_columna = f"precio_{tipo_precio}"
            cursor.execute(f"SELECT id, nombre, stock, {precio_columna} as precio FROM productos WHERE id = %s", (item.producto_id,))
            prod = cursor.fetchone()
            
            if not prod:
                raise HTTPException(status_code=400, detail=f"Producto ID {item.producto_id} no encontrado")
                
            if prod["stock"] < item.cantidad:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para {prod['nombre']}")
            
            subtotal = prod["precio"] * item.cantidad
            total_pedido += subtotal
            detalle_items.append(f"[ID:{prod['id']}] {item.cantidad}x {prod['nombre']} (${subtotal})")
            
        for item in pedido.items:
            cursor.execute("UPDATE productos SET stock = stock - %s WHERE id = %s", (item.cantidad, item.producto_id))
            
        detalle_texto = ", ".join(detalle_items) + f" | **TOTAL: ${total_pedido}**"
        
        cursor.execute(
            "INSERT INTO pedidos (cliente_nombre, lista_precio, detalle, estado) VALUES (%s, %s, %s, 'pendiente')",
            (pedido.cliente_nombre.strip(), tipo_precio, detalle_texto)
        )
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))
        
    cursor.close()
    conn.close()
    
    return {"mensaje": "Pedido registrado con éxito"}

@app.get("/api/pedidos")
def listar_pedidos(cliente_nombre: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if cliente_nombre:
        cursor.execute("SELECT id, cliente_nombre, lista_precio, detalle, estado, fecha FROM pedidos WHERE cliente_nombre ILIKE %s ORDER BY id DESC", (f"%{cliente_nombre}%",))
    else:
        cursor.execute("SELECT id, cliente_nombre, lista_precio, detalle, estado, fecha FROM pedidos ORDER BY id DESC")
    pedidos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [
        {
            "id": p["id"],
            "cliente": p["cliente_nombre"],
            "lista_precio": p["lista_precio"],
            "detalle": p["detalle"],
            "estado": p["estado"],
            "fecha": str(p["fecha"]) if p["fecha"] else ""
        }
        for p in pedidos
    ]

class EstadoActualizacion(BaseModel):
    estado: str

@app.put("/api/pedidos/{pedido_id}/estado")
def actualizar_estado_pedido(pedido_id: int, data: EstadoActualizacion):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pedidos SET estado = %s WHERE id = %s", (data.estado, pedido_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Estado actualizado con éxito"}

@app.delete("/api/pedidos/{pedido_id}")
def eliminar_pedido(pedido_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT detalle FROM pedidos WHERE id = %s", (pedido_id,))
    pedido = cursor.fetchone()
    
    if not pedido:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
    detalle = pedido["detalle"]
    matches = re.findall(r'\[ID:(\d+)\]\s+(\d+)x', detalle)
    for prod_id_str, cantidad_str in matches:
        prod_id = int(prod_id_str)
        cantidad = int(cantidad_str)
        cursor.execute("UPDATE productos SET stock = stock + %s WHERE id = %s", (cantidad, prod_id))
        
    cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"mensaje": "Pedido eliminado y stock devuelto correctamente"}