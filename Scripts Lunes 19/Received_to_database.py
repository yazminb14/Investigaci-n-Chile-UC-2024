import can
import struct
import json
import os
import sqlite3
from datetime import datetime

def convert_from_8_bytes_float(data_bytes):
    # Convertir 8 bytes en formato de punto flotante de 64 bits a un número decimal
    return struct.unpack('>d', data_bytes)[0]

def create_initial_json_file():
    # Crear un archivo JSON con la estructura inicial si no existe
    data = {
        "VehicleData": {
            "BatterySystem": [
                {"sensor_name": "SOC", "can_id": "16777216", "timestamp": None, "value": None},
                {"sensor_name": "BatPowerLosses", "can_id": "16777217", "timestamp": None, "value": None},
                {"sensor_name": "BatteryVoltage", "can_id": "16777218", "timestamp": None, "value": None},
                {"sensor_name": "BatteryPower", "can_id": "16777219", "timestamp": None, "value": None},
                {"sensor_name": "BatteryCurrent", "can_id": "16777220", "timestamp": None, "value": None}
            ],
            "MotorSystem": [
                {"sensor_name": "MotorPowerOut", "can_id": "33554432", "timestamp": None, "value": None},
                {"sensor_name": "MotorPowerIn", "can_id": "33554433", "timestamp": None, "value": None},
                {"sensor_name": "MotorPowerLosses", "can_id": "33554434", "timestamp": None, "value": None},
                {"sensor_name": "MotorNetTorque", "can_id": "33554435", "timestamp": None, "value": None}
            ],
            "DrivelineSystem": [
                {"sensor_name": "DrivelinePowerLoss", "can_id": "50331648", "timestamp": None, "value": None},
                {"sensor_name": "MotorSpeed", "can_id": "50331649", "timestamp": None, "value": None},
                {"sensor_name": "NetTractiveForce", "can_id": "50331650", "timestamp": None, "value": None}
            ],
            "GliderSystem": [
                {"sensor_name": "VehicleSpeed", "can_id": "67108864", "timestamp": None, "value": None}
            ]
        }
    }

    with open('received_data.json', 'w') as file:
        json.dump(data, file, indent=4)

def create_database():
    # Crear la base de datos SQLite y las tablas necesarias si no existen
    conn = sqlite3.connect('vehicle_data.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS can_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        can_id TEXT NOT NULL,
        sensor_name TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        value REAL NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def save_to_database(can_id, sensor_name, timestamp, value):
    # Guardar los datos en la base de datos SQLite
    conn = sqlite3.connect('vehicle_data.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO can_data (can_id, sensor_name, timestamp, value)
    VALUES (?, ?, ?, ?)
    ''', (can_id, sensor_name, timestamp, value))
    conn.commit()
    conn.close()

def fetch_and_display_all_data(print_header=True):
    # Función para obtener y mostrar todas las filas de la base de datos
    conn = sqlite3.connect('vehicle_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM can_data')
    rows = cursor.fetchall()
    
    if print_header:
        # Imprimir solo una vez los nombres de las columnas
        print("ID | CAN ID     | Sensor Name     | Timestamp              | Value")
        print("---------------------------------------------------------------")
    
    # Mostrar las filas en un formato legible
    for row in rows:
        print(f"{row[0]:<3} | {row[1]:<10} | {row[2]:<14} | {row[3]:<20} | {row[4]}")
    
    conn.close()


def save_to_json(can_id, decimal_value):
    # Leer datos existentes del archivo JSON
    if os.path.exists('received_data.json'):
        try:
            with open('received_data.json', 'r') as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            print("Error al leer el archivo JSON. Creando un nuevo archivo.")
            create_initial_json_file()
            with open('received_data.json', 'r') as file:
                existing_data = json.load(file)
    else:
        create_initial_json_file()
        with open('received_data.json', 'r') as file:
            existing_data = json.load(file)

    # Asegurarse de que la clave 'VehicleData' existe
    if 'VehicleData' not in existing_data:
        print("'VehicleData' no encontrado en los datos. Creando la estructura inicial.")
        create_initial_json_file()
        with open('received_data.json', 'r') as file:
            existing_data = json.load(file)

    # Obtener el sistema correcto basado en el ID
    systems = {
        "16777216": "BatterySystem",
        "16777217": "BatterySystem",
        "16777218": "BatterySystem",
        "16777219": "BatterySystem",
        "16777220": "BatterySystem",
        "33554432": "MotorSystem",
        "33554433": "MotorSystem",
        "33554434": "MotorSystem",
        "33554435": "MotorSystem",
        "50331648": "DrivelineSystem",
        "50331649": "DrivelineSystem",
        "50331650": "DrivelineSystem",
        "67108864": "GliderSystem"
    }
    
    system_name = systems.get(str(can_id), None)
    if system_name:
        timestamp = datetime.utcnow().isoformat()
        found = False
        for sensor in existing_data["VehicleData"].get(system_name, []):
            if sensor["can_id"] == str(can_id):
                sensor["timestamp"] = timestamp
                sensor["value"] = decimal_value
                # Guardar en la base de datos
                save_to_database(sensor["can_id"], sensor["sensor_name"], timestamp, decimal_value)
                found = True
                break
        if not found:
            print(f"No se encontró un sensor con el ID {can_id} en {system_name}")
    else:
        print(f"ID de CAN {can_id} no mapeado a ningún sistema")

    # Guardar los datos actualizados en el archivo JSON
    with open('received_data.json', 'w') as file:
        json.dump(existing_data, file, indent=4)

def receive_can_message():
    create_database()  # Asegurar que la base de datos esté creada

    try:
        # Configurar la interfaz CAN
        bus = can.interface.Bus(channel='can0', bustype='socketcan')
        print("Interfaz CAN configurada correctamente, esperando mensajes...")

        print_header = True  # Controla la impresión del encabezado
        
        while True:
            # Recibir mensaje
            message = bus.recv()
            if message:
                # Verificar si el mensaje tiene 8 bytes de datos
                if len(message.data) == 8:
                    # Convertir los datos a punto flotante de 64 bits
                    decimal_value = convert_from_8_bytes_float(message.data)
                    print(f"ID: {message.arbitration_id}, Decimal Value: {decimal_value}, Extended: {message.is_extended_id}")

                    # Guardar el valor decimal en el archivo JSON y base de datos
                    save_to_json(message.arbitration_id, decimal_value)

                    # Mostrar todas las filas de la base de datos sin repetir encabezados
                    fetch_and_display_all_data(print_header)
                    print_header = False  # Desactivar encabezados después de la primera impresión
                else:
                    print(f"ID: {message.arbitration_id}, Data: {message.data}, Extended: {message.is_extended_id} (Datos no tienen 8 bytes)")

    except can.CanInterfaceNotImplementedError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)

if __name__ == "__main__":
    receive_can_message()

