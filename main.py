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
            # Buscar el precio según la lista seleccionada
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
            
        # Descontar stock
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