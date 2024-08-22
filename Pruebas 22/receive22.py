import time
import struct
import can
import json
import os
import sqlite3
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure
from collections import defaultdict

# Cargar variables de entorno para la conexión MongoDB
load_dotenv()
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")

# Configurar la conexión a MongoDB
client = MongoClient(f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/")
db = client["VehicleData"]

# Probar la conexión a MongoDB
try:
    client.admin.command('ping')
    print("Conexión exitosa a MongoDB")
except ConnectionFailure:
    print("No se pudo conectar a MongoDB")


def convert_from_8_bytes_float(data_bytes):
    # Convertir 8 bytes en formato de punto flotante de 64 bits a un número decimal
    return struct.unpack('>d', data_bytes)[0]


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


def save_to_mongo(can_id, sensor_name, timestamp, value):
    # Guardar los datos en MongoDB
    document = {
        "can_id": can_id,
        "sensor_name": sensor_name,
        "timestamp": timestamp,
        "value": value
    }
    
    # Seleccionar la colección basada en el sistema
    systems_map = {
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
    
    collection_name = systems_map.get(str(can_id), "UnknownSystem")

    # Intentar la inserción y capturar posibles errores
    try:
        db[collection_name].insert_one(document)
        print(f"Enviado a MongoDB - Colección: {collection_name}, Documento: {document}")
    except Exception as e:
        print(f"Error al enviar a MongoDB: {e}")


def save_to_json(can_id, timestamp, decimal_value):
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
        found = False
        for sensor in existing_data["VehicleData"].get(system_name, []):
            if sensor["can_id"] == str(can_id):
                sensor["timestamp"] = timestamp.isoformat()  # Guardar como ISO format
                sensor["value"] = decimal_value
                # Guardar en MongoDB
                save_to_mongo(sensor["can_id"], sensor["sensor_name"], timestamp.isoformat(), decimal_value)
                found = True
                break
        if not found:
            print(f"No se encontró un sensor con el ID {can_id} en {system_name}")
    else:
        print(f"ID de CAN {can_id} no mapeado a ningún sistema")


def receive_can_message():
    create_database()  # Asegurar que la base de datos esté creada

    # Estructura para almacenar temporalmente valores y timestamps
    pending_messages = defaultdict(lambda: {"value": None, "timestamp": None})

    try:
        # Configurar la interfaz CAN
        bus = can.Bus(channel='can0', bustype='socketcan')
        print("Interfaz CAN configurada correctamente, esperando mensajes...")

        while True:
            # Recibir mensaje
            message = bus.recv()
            if message:
                can_id = message.arbitration_id

                # Verificar si el mensaje tiene 8 bytes de datos
                if len(message.data) == 8:
                    # Si el ID del mensaje es para el valor del sensor (por debajo de cierto umbral)
                    if can_id < 0x1000:
                        decimal_value = convert_from_8_bytes_float(message.data)
                        pending_messages[can_id]["value"] = decimal_value

                    # Si el ID del mensaje es para el timestamp (ID con un offset)
                    else:
                        timestamp = convert_from_8_bytes_float(message.data)
                        pending_messages[can_id - 0x1000]["timestamp"] = datetime.fromtimestamp(timestamp)

                    # Verificar si tenemos tanto el valor como el timestamp
                    if pending_messages[can_id]["value"] is not None and pending_messages[can_id]["timestamp"] is not None:
                        # Procesar los datos completos
                        save_to_json(can_id, pending_messages[can_id]["timestamp"], pending_messages[can_id]["value"])

                        # Limpiar los datos pendientes
                        pending_messages.pop(can_id)

    except can.CanError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)


if __name__ == "__main__":
    receive_can_message()
