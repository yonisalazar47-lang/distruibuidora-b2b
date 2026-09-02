from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import psycopg2
import psycopg2.extras

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Obtenemos la URL de conexión desde las variables de entorno de Render
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    # PostgreSQL maneja las conexiones mediante psycopg2
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            tipo_precio TEXT DEFAULT '1'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL,
            precio_1 REAL NOT NULL,
            precio_2 REAL NOT NULL,
            precio_3 REAL NOT NULL,
            precio_4 REAL NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER,
            cliente_nombre TEXT,
            detalle TEXT,
            estado TEXT DEFAULT 'pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    """)
    
    # Datos iniciales si las tablas están vacías
    cursor.execute("SELECT COUNT(*) as total FROM clientes")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("INSERT INTO clientes (usuario, password, nombre, tipo_precio) VALUES ('cliente1', '1234', 'Kiosco Minorista', '1')")
        cursor.execute("INSERT INTO clientes (usuario, password, nombre, tipo_precio) VALUES ('cliente2', '1234', 'Super Mayorista S.A.', '2')")
    
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
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "El archivo index.html no se encontró."

@app.get("/admin.html", response_class=HTMLResponse)
def leer_admin():
    if os.path.exists("admin.html"):
        with open("admin.html", "r", encoding="utf-8") as f:
            return f.read()
    return "El archivo admin.html no se encontró."

@app.get("/vendedor.html", response_class=HTMLResponse)
def leer_vendedor():
    if os.path.exists("vendedor.html"):
        with open("vendedor.html", "r", encoding="utf-8") as f:
            return f.read()
    return "El archivo vendedor.html no se encontró."

class CredencialesLogin(BaseModel):
    usuario: str
    password: str

@app.post("/api/login")
def login_cliente(credenciales: CredencialesLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, tipo_precio FROM clientes WHERE usuario = %s AND password = %s", 
        (credenciales.usuario, credenciales.password)
    )
    cliente = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not cliente:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
    return {
        "id": cliente["id"],
        "nombre": cliente["nombre"],
        "tipo_precio": cliente["tipo_precio"] if cliente["tipo_precio"] else "1"
    }

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

class ClienteNuevo(BaseModel):
    usuario: str
    password: str
    nombre: str
    tipo_precio: str

@app.post("/api/clientes")
def crear_cliente(c: ClienteNuevo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO clientes (usuario, password, nombre, tipo_precio) VALUES (%s, %s, %s, %s)",
            (c.usuario, c.password, c.nombre, c.tipo_precio)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    finally:
        cursor.close()
        conn.close()
    return {"mensaje": "Cliente creado con éxito"}

class ItemPedido(BaseModel):
    producto_id: int
    cantidad: int

class PedidoEntrante(BaseModel):
    cliente_id: int
    items: List[ItemPedido]

@app.post("/api/pedidos")
def registrar_pedido(pedido: PedidoEntrante):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT nombre, tipo_precio FROM clientes WHERE id = %s", (pedido.cliente_id,))
    cli = cursor.fetchone()
    if not cli:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Cliente no encontrado")
        
    cliente_nombre = cli["nombre"]
    tipo_precio = cli["tipo_precio"] if cli["tipo_precio"] else "1"
    
    detalle_items = []
    total_pedido = 0.0
    
    for item in pedido.items:
        cursor.execute(f"SELECT nombre, stock, precio_{tipo_precio} as precio FROM productos WHERE id = %s", (item.producto_id,))
        prod = cursor.fetchone()
        if not prod or prod["stock"] < item.cantidad:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para el producto ID {item.producto_id}")
        
        subtotal = prod["precio"] * item.cantidad
        total_pedido += subtotal
        detalle_items.append(f"{item.cantidad}x {prod['nombre']} (${subtotal})")
        
    for item in pedido.items:
        cursor.execute("UPDATE productos SET stock = stock - %s WHERE id = %s", (item.cantidad, item.producto_id))
        
    detalle_texto = ", ".join(detalle_items) + f" | **TOTAL: ${total_pedido}**"
    
    cursor.execute(
        "INSERT INTO pedidos (cliente_id, cliente_nombre, detalle, estado) VALUES (%s, %s, %s, 'pendiente')",
        (pedido.cliente_id, cliente_nombre, detalle_texto)
    )
    
    conn.commit()
    cursor.execute("SELECT LASTVAL()")
    res_id = cursor.fetchone()
    pedido_id = res_id['lastval'] if res_id else 1
    
    cursor.close()
    conn.close()
    
    return {"pedido_id": pedido_id, "mensaje": "Pedido registrado con éxito"}

@app.get("/api/pedidos")
def listar_pedidos(cliente_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if cliente_id:
        cursor.execute("SELECT id, cliente_nombre, detalle, estado, fecha FROM pedidos WHERE cliente_id = %s ORDER BY id DESC", (cliente_id,))
    else:
        cursor.execute("SELECT id, cliente_nombre, detalle, estado, fecha FROM pedidos ORDER BY id DESC")
    pedidos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [
        {
            "id": p["id"],
            "cliente": p["cliente_nombre"],
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
