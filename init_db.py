import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Elimina tablas anteriores para limpiar incompatibilidades
    cursor.execute("DROP TABLE IF EXISTS productos")
    cursor.execute("DROP TABLE IF EXISTS pedidos")

    # Recrea la tabla de productos
    cursor.execute('''
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL,
            precio REAL DEFAULT 0.0
        )
    ''')

    # Recrea la tabla de pedidos
    cursor.execute('''
        CREATE TABLE pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            lista_precio INTEGER DEFAULT 1,
            detalle TEXT NOT NULL,
            estado TEXT DEFAULT 'pendiente'
        )
    ''')

    # Inserta productos de prueba
    cursor.executemany('''
        INSERT INTO productos (nombre, stock, precio) VALUES (?, ?, ?)
    ''', [
        ('Producto Demo 1', 50, 1500.0),
        ('Producto Demo 2', 20, 2500.0)
    ])

    # Inserta pedidos de prueba
    cursor.executemany('''
        INSERT INTO pedidos (cliente, lista_precio, detalle, estado) VALUES (?, ?, ?, ?)
    ''', [
        ('Cliente Prueba A', 1, '2x Producto Demo 1', 'pendiente'),
        ('Cliente Prueba B', 2, '1x Producto Demo 2', 'entregado')
    ])

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()