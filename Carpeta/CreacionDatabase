import sqlite3

def initialize_db():
    # Conectar a la base de datos (se creará si no existe)
    conn = sqlite3.connect('vehicle_data.db')
    cursor = conn.cursor()

    # Crear las tablas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS BatterySystem (
        id INTEGER PRIMARY KEY,
        sensor_name TEXT,
        can_id INTEGER,
        timestamp TEXT,
        value REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MotorSystem (
        id INTEGER PRIMARY KEY,
        sensor_name TEXT,
        can_id INTEGER,
        timestamp TEXT,
        value REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS DrivelineSystem (
        id INTEGER PRIMARY KEY,
        sensor_name TEXT,
        can_id INTEGER,
        timestamp TEXT,
        value REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS GliderSystem (
        id INTEGER PRIMARY KEY,
        sensor_name TEXT,
        can_id INTEGER,
        timestamp TEXT,
        value REAL
    )
    ''')

    # Guardar cambios y cerrar la conexión
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
