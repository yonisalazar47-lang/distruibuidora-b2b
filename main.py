from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect("distribuidora.db")
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar base de datos con las tablas y 4 precios por producto
@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            tipo_precio TEXT DEFAULT '1'
        )
    """)
    
    # Tabla de productos adaptada para 4 precios (ej: 1=Minorista, 2=Mayorista, 3=Distribuidor, 4=Especial)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL,
            precio_1 REAL NOT NULL,
            precio_2 REAL NOT NULL,
            precio_3 REAL NOT NULL,
            precio_4 REAL NOT NULL
        )
    """)
    
    # Usuarios de prueba (tipo_precio puede ser '1', '2', '3' o '4')
    cursor.execute("INSERT OR IGNORE INTO clientes (id, usuario, password, nombre, tipo_precio) VALUES (1, 'cliente1', '1234', 'Kiosco Minorista', '1')")
    cursor.execute("INSERT OR IGNORE INTO clientes (id, usuario, password, nombre, tipo_precio) VALUES (2, 'cliente2', '1234', 'Super Mayorista S.A.', '2')")
    
    # Producto de prueba con 4 precios distintos
    cursor.execute("INSERT OR IGNORE INTO productos (id, nombre, stock, precio_1, precio_2, precio_3, precio_4) VALUES (1, 'Harina 1kg', 100, 1000.0, 800.0, 700.0, 600.0)")
    
    conn.commit()
    conn.close()

# Ruta raíz para cargar el portal de pedidos automáticamente
@app.get("/", response_class=HTMLResponse)
def leer_raiz():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "Bienvenido a la API de Distribuidora B2B."

class CredencialesLogin(BaseModel):
    usuario: str
    password: str

@app.post("/api/login")
def login_cliente(credenciales: CredencialesLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, tipo_precio FROM clientes WHERE usuario = ? AND password = ?", 
        (credenciales.usuario, credenciales.password)
    )
    cliente = cursor.fetchone()
    conn.close()
    
    if not cliente:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
    return {
        "id": cliente["id"],
        "nombre": cliente["nombre"],
        "tipo_precio": cliente["tipo_precio"] if cliente["tipo_precio"] else "1"
    }

# Endpoint para listar productos seleccionando el precio correcto según el nivel (1 al 4)
@app.get("/api/productos")
def listar_productos(tipo_precio: str = "1"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, stock, precio_1, precio_2, precio_3, precio_4 FROM productos")
    productos = cursor.fetchall()
    conn.close()
    
    lista_resultado = []
    for p in productos:
        # Seleccionamos qué precio mostrar según el nivel del cliente
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

# Modelos para dar de alta nuevos registros desde la web
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
        "INSERT INTO productos (nombre, stock, precio_1, precio_2, precio_3, precio_4) VALUES (?, ?, ?, ?, ?, ?)",
        (p.nombre, p.stock, p.precio_1, p.precio_2, p.precio_3, p.precio_4)
    )
    conn.commit()
    conn.close()
    return {"mensaje": "Producto creado con éxito"}
# Ruta específica para servir el panel de administración
@app.get("/admin.html", response_class=HTMLResponse)
def leer_admin():
    if os.path.exists("admin.html"):
        with open("admin.html", "r", encoding="utf-8") as f:
            return f.read()
    return "El archivo admin.html no se encontró en el servidor."
from pydantic import BaseModel

# Modelo para recibir el cliente nuevo
class ClienteNuevo(BaseModel):
    usuario: str
    password: str
    nombre: str
    tipo_precio: str

# Endpoint para registrar el cliente en la base de datos
@app.post("/api/clientes")
def crear_cliente(c: ClienteNuevo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO clientes (usuario, password, nombre, tipo_precio) VALUES (?, ?, ?, ?)",
            (c.usuario, c.password, c.nombre, c.tipo_precio)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    finally:
        conn.close()
    return {"mensaje": "Cliente creado con éxito"}
# Endpoint para que el panel de administración vea todos los detalles y stock
@app.get("/api/productos-admin")
def listar_productos_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, stock, precio_1, precio_2, precio_3, precio_4 FROM productos")
    productos = cursor.fetchall()
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