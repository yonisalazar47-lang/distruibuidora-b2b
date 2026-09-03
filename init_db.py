import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Tabla de Productos con 4 precios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL,
            precio_1 REAL DEFAULT 0.0,
            precio_2 REAL DEFAULT 0.0,
            precio_3 REAL DEFAULT 0.0,
            precio_4 REAL DEFAULT 0.0
        )
    ''')

    # Tabla de Pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            lista_precio INTEGER DEFAULT 1,
            detalle TEXT NOT NULL,
            estado TEXT DEFAULT 'pendiente'
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()