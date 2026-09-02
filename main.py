from pydantic import BaseModel
from typing import List

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
    
    total_pedido = 0.0
    
    # Validar stock y calcular total (aquí podríamos verificar el tipo de precio del cliente si se desea afinar)
    for item in pedido.items:
        cursor.execute("SELECT stock, precio_1 FROM productos WHERE id = ?", (item.producto_id,))
        prod = cursor.fetchone()
        if not prod or prod["stock"] < item.cantidad:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para el producto ID {item.producto_id}")
            
    # Registrar el pedido y descontar stock
    cursor.execute("INSERT INTO clientes (id) VALUES (?)", (pedido.cliente_id,)) # O una tabla de pedidos si la tienes creada
    # Descontar stock de la tabla productos
    for item in pedido.items:
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (item.cantidad, item.producto_id))
        
    conn.commit()
    conn.close()
    
    return {"pedido_id": 1001, "total": 0.0, "mensaje": "Pedido registrado con éxito"}