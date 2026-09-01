from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="API Distribuidora B2B")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "distribuidora.db"

# Modelos de datos
class LoginRequest(BaseModel):
    usuario: str
    password: str

class ItemPedido(BaseModel):
    producto_id: int
    cantidad: int

class PedidoCreate(BaseModel):
    cliente_id: int
    items: list[ItemPedido]

# Servir la interfaz web principal en la raíz
@app.get("/")
def leer_raiz():
    return FileResponse("index.html")

# Endpoint de Login
@app.post("/api/login")
def login_cliente(data: LoginRequest):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, nombre_comercio, lista_id 
        FROM clientes 
        WHERE usuario = ? AND password_hash = ?
    """, (data.usuario, data.password))
    
    cliente = cursor.fetchone()
    conn.close()

    if not cliente:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

    return {
        "mensaje": "Login exitoso",
        "cliente_id": cliente[0],
        "nombre_comercio": cliente[1],
        "lista_id": cliente[2]
    }

# Endpoint de Catálogo filtrado por la lista del cliente
@app.get("/api/catalogo/{lista_id}")
def obtener_catalogo(lista_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, p.nombre, p.stock, pr.precio
        FROM productos p
        JOIN precios_productos pr ON p.id = pr.producto_id
        WHERE pr.lista_id = ? AND p.activo = 1
    """, (lista_id,))
    
    productos = [
        {
            "producto_id": row[0],
            "nombre": row[1],
            "stock": row[2],
            "precio": row[3]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return productos

# Endpoint para crear pedidos y descontar stock
@app.post("/api/pedidos")
def crear_pedido(pedido: PedidoCreate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # 1. Obtener la lista de precios del cliente para calcular el total exacto
        cursor.execute("SELECT lista_id FROM clientes WHERE id = ?", (pedido.cliente_id,))
        res_cliente = cursor.fetchone()
        if not res_cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        lista_id = res_cliente[0]
        total_pedido = 0.0
        detalles_calculados = []

        # 2. Validar stock y calcular subtotales
        for item in pedido.items:
            cursor.execute("SELECT stock FROM productos WHERE id = ?", (item.producto_id,))
            res_prod = cursor.fetchone()
            if not res_prod or res_prod[0] < item.cantidad:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para el producto ID {item.producto_id}")
            
            cursor.execute("SELECT precio FROM precios_productos WHERE producto_id = ? AND lista_id = ?", (item.producto_id, lista_id))
            res_precio = cursor.fetchone()
            if not res_precio:
                raise HTTPException(status_code=400, detail=f"Precio no configurado para el producto {item.producto_id}")
            
            precio_unitario = res_precio[0]
            total_pedido += precio_unitario * item.cantidad
            detalles_calculados.append((item.producto_id, item.cantidad, precio_unitario))

        # 3. Registrar el pedido principal
        cursor.execute("INSERT INTO pedidos (cliente_id, total, estado) VALUES (?, ?, 'Pendiente')", (pedido.cliente_id, total_pedido))
        pedido_id = cursor.lastrowid

        # 4. Insertar el detalle y descontar stock en tiempo real
        for prod_id, cant, precio_u in detalles_calculados:
            cursor.execute("INSERT INTO detalle_pedidos (pedido_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)", (pedido_id, prod_id, cant, precio_u))
            cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cant, prod_id))

        conn.commit()
        return {"mensaje": "Pedido creado con éxito", "pedido_id": pedido_id, "total": total_pedido}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
# Endpoint para que el vendedor liste todos los pedidos
@app.get("/api/pedidos")
def listar_pedidos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, c.nombre_comercio, p.total, p.estado, p.fecha
        FROM pedidos p
        JOIN clientes c ON p.cliente_id = c.id
        ORDER BY p.id DESC
    """)
    
    pedidos = [
        {
            "pedido_id": row[0],
            "nombre_comercio": row[1],
            "total": row[2],
            "estado": row[3],
            "fecha": row[4]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return pedidos
# Servir la pantalla del panel de vendedores
@app.get("/admin.html")
def leer_admin():
    return FileResponse("admin.html")
from pydantic import BaseModel

# Modelo para actualizar estado
class EstadoUpdate(BaseModel):
    estado: str

# 1. Endpoint para actualizar el estado del pedido
@app.put("/api/pedidos/{pedido_id}/estado")
def actualizar_estado_pedido(pedido_id: int, data: EstadoUpdate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (data.estado, pedido_id))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Estado actualizado con éxito"}

# 2. Endpoint para obtener el detalle de los productos de un pedido
@app.get("/api/pedidos/{pedido_id}/detalle")
def obtener_detalle_pedido(pedido_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.nombre, dp.cantidad, dp.precio_unitario, (dp.cantidad * dp.precio_unitario) as subtotal
        FROM detalle_pedidos dp
        JOIN productos p ON dp.producto_id = p.id
        WHERE dp.pedido_id = ?
    """, (pedido_id,))
    
    detalles = [
        {
            "producto": row[0],
            "cantidad": row[1],
            "precio_unitario": row[2],
            "subtotal": row[3]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return detalles
# Reporte de ventas agrupadas por Mes
@app.get("/api/reportes/mensual")
def reporte_mensual():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Agrupa por Año-Mes usando la fecha del pedido
    cursor.execute("""
        SELECT strftime('%Y-%m', fecha) as mes, COUNT(id) as total_pedidos, SUM(total) as ingresos_totales
        FROM pedidos
        WHERE estado != 'Cancelado'
        GROUP BY mes
        ORDER BY mes DESC
    """)
    
    reporte = [
        {"periodo": row[0], "total_pedidos": row[1], "ingresos_totales": row[2]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return reporte

# Reporte de ventas agrupadas por Año
@app.get("/api/reportes/anual")
def reporte_anual():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Agrupa por Año usando la fecha del pedido
    cursor.execute("""
        SELECT strftime('%Y', fecha) as anio, COUNT(id) as total_pedidos, SUM(total) as ingresos_totales
        FROM pedidos
        WHERE estado != 'Cancelado'
        GROUP BY anio
        ORDER BY anio DESC
    """)
    
    reporte = [
        {"periodo": row[0], "total_pedidos": row[1], "ingresos_totales": row[2]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return reporte
from typing import Optional

# Endpoint de pedidos actualizado con filtros de fecha opcionales
@app.get("/api/pedidos")
def listar_pedidos(desde: Optional[str] = None, hasta: Optional[str] = None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = """
        SELECT p.id, c.nombre_comercio, p.total, p.estado, p.fecha
        FROM pedidos p
        JOIN clientes c ON p.cliente_id = c.id
    """
    params = []
    
    if desde and hasta:
        query += " WHERE date(p.fecha) BETWEEN ? AND ?"
        params.extend([desde, hasta])
        
    query += " ORDER BY p.id DESC"
    
    cursor.execute(query, params)
    
    pedidos = [
        {
            "pedido_id": row[0],
            "nombre_comercio": row[1],
            "total": row[2],
            "estado": row[3],
            "fecha": row[4]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return pedidos