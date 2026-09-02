from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Configurar CORS para permitir que tu frontend (index.html / admin.html) se conecte
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

# Modelo para recibir los datos del Login
class CredencialesLogin(BaseModel):
    usuario: str
    password: str

# 1. Endpoint de Login que devuelve el tipo de precio del cliente
@app.post("/api/login")
def login_cliente(credenciales: CredencialesLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buscamos al cliente y su categoría de precio (ej. 'general', 'mayorista', etc.)
    # Si tu tabla no tiene 'tipo_precio' aún, puedes asegurarte de crearla o manejar un valor por defecto.
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
        "tipo_precio": cliente["tipo_precio"] if "tipo_precio" in cliente.keys() and cliente["tipo_precio"] else "general"
    }

# 2. Endpoint para listar productos adaptando el precio según el cliente
@app.get("/api/productos")
def listar_productos(tipo_precio: str = "general"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Asegúrate de que tu tabla 'productos' tenga las columnas 'precio' y 'precio_mayorista'
    cursor.execute("SELECT id, nombre, stock, precio, precio_mayorista FROM productos")
    productos = cursor.fetchall()
    conn.close()
    
    lista_resultado = []
    for p in productos:
        # Definimos qué precio mostrar según la categoría del cliente
        # Si es mayorista y existe un precio mayorista cargado (> 0), se usa ese; si no, el precio base.
        precio_final = p["precio"]
        if tipo_precio == "mayorista" and p["precio_mayorista"] is not None and p["precio_mayorista"] > 0:
            precio_final = p["precio_mayorista"]
            
        lista_resultado.append({
            "id": p["id"],
            "nombre": p["nombre"],
            "stock": p["stock"],
            "precio": precio_final
        })
        
    return lista_resultado
def inicializar_bd_si_no_existe():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tablas por si están vacías
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            tipo_precio TEXT DEFAULT 'general'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL,
            precio REAL NOT NULL,
            precio_mayorista REAL DEFAULT 0
        )
    """)
    
    # Insertar usuarios de prueba por defecto
    cursor.execute("INSERT OR IGNORE INTO clientes (id, usuario, password, nombre, tipo_precio) VALUES (1, 'cliente1', '1234', 'Kiosco Minorista', 'general')")
    cursor.execute("INSERT OR IGNORE INTO clientes (id, usuario, password, nombre, tipo_precio) VALUES (2, 'cliente2', '1234', 'Super Mayorista S.A.', 'mayorista')")
    
    # Insertar un producto de prueba con ambos precios
    cursor.execute("INSERT OR IGNORE INTO productos (id, nombre, stock, precio, precio_mayorista) VALUES (1, 'Harina 1kg', 100, 1000.0, 800.0)")
    
    conn.commit()
    conn.close()

# Ejecutar esto justo al iniciar la app de FastAPI
inicializar_bd_si_no_existe()