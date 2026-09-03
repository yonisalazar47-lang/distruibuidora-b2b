import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Recrear tabla de productos con soporte para las 4 listas
    cursor.execute("DROP TABLE IF EXISTS productos")
    cursor.execute('''
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL,
            precio_1 REAL DEFAULT 0.0,
            precio_2 REAL DEFAULT 0.0,
            precio_3 REAL DEFAULT 0.0,
            precio_4 REAL DEFAULT 0.0
        )
    ''')

    # Recrear tabla de pedidos
    cursor.execute("DROP TABLE IF EXISTS pedidos")
    cursor.execute('''
        CREATE TABLE pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            lista_precio INTEGER DEFAULT 1,
            detalle TEXT NOT NULL,
            estado TEXT DEFAULT 'pendiente'
        )
    ''')

    # Cargar tus productos reales
    cursor.executemany('''
        INSERT INTO productos (nombre, stock, precio_1, precio_2, precio_3, precio_4) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        ('Harina 1kg', 90, 600.0, 650.0, 700.0, 750.0),
        ('COCA COLA 2.25 LT', 50, 3000.0, 3100.0, 3200.0, 3300.0),
        ('SPRITE 2.25 LT', 40, 2900.0, 3000.0, 3100.0, 3200.0)
    ])

    # Cargar un pedido inicial para verificar la lista de pedidos
    cursor.execute('''
        INSERT INTO pedidos (cliente, lista_precio, detalle, estado)
        VALUES ('DEISI', 4, '[ID:1] 1x Harina 1kg ($600.0), [ID:2] 1x COCA COLA 2.25 LT ($3000.0) | TOTAL: $3600.0', 'entregado')
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()