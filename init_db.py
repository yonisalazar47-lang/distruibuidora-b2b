import sqlite3

DB_NAME = "distribuidora.db"

def inicializar_base_datos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Crear las tablas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS listas_precios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_lista TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        activo BOOLEAN DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS precios_productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER REFERENCES productos(id) ON DELETE CASCADE,
        lista_id INTEGER REFERENCES listas_precios(id) ON DELETE CASCADE,
        precio REAL NOT NULL,
        UNIQUE(producto_id, lista_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_comercio TEXT NOT NULL,
        usuario TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        lista_id INTEGER REFERENCES listas_precios(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER REFERENCES clientes(id),
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        estado TEXT DEFAULT 'Pendiente',
        total REAL NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalle_pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
        producto_id INTEGER REFERENCES productos(id),
        cantidad INTEGER NOT NULL,
        precio_unitario REAL NOT NULL
    );
    """)

    # 2. Insertar datos de prueba (si las tablas están vacías)
    cursor.execute("SELECT COUNT(*) FROM listas_precios")
    if cursor.fetchone()[0] == 0:
        print("Cargando datos de prueba...")
        
        # Las 4 listas de precios
        cursor.executemany("INSERT INTO listas_precios (nombre_lista) VALUES (?)", [
            ("Mayorista A",),
            ("Mayorista B",),
            ("Minorista",),
            ("Distribuidor Oficial",)
        ])

        # Productos de ejemplo con un stock único centralizado
        cursor.executemany("INSERT INTO productos (nombre, stock) VALUES (?, ?)", [
            ("Azúcar 1kg", 500),
            ("Yerba Mate 1kg", 300),
            ("Aceite de Girasol 1.5L", 200)
        ])

        # Precios diferenciados por cada lista para cada producto
        # (Producto 1: Azúcar -> Precios según lista 1, 2, 3, 4)
        cursor.executemany("INSERT INTO precios_productos (producto_id, lista_id, precio) VALUES (?, ?, ?)", [
            (1, 1, 1200.00), # Azúcar Lista 1
            (1, 2, 1250.00), # Azúcar Lista 2
            (1, 3, 1400.00), # Azúcar Lista 3
            (1, 4, 1100.00), # Azúcar Lista 4
            
            # (Producto 2: Yerba)
            (2, 1, 3500.00),
            (2, 2, 3650.00),
            (2, 3, 3900.00),
            (2, 4, 3300.00),

            # (Producto 3: Aceite)
            (3, 1, 2200.00),
            (3, 2, 2300.00),
            (3, 3, 2500.00),
            (3, 4, 2050.00),
        ])

        # Clientes de prueba (asignados a distintas listas)
        cursor.executemany("INSERT INTO clientes (nombre_comercio, usuario, password_hash, lista_id) VALUES (?, ?, ?, ?)", [
            ("Supermercado El Barato", "cliente1", "1234", 1), # Ve lista 1
            ("Almacén Doña Rosa", "cliente2", "1234", 2),      # Ve lista 2
        ])

        conn.commit()
        print("¡Datos de prueba cargados con éxito!")
    
    conn.close()

if __name__ == "__main__":
    inicializar_base_datos()