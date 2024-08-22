import time
import struct
import can
import json
import os
import sqlite3
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
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
    return struct.unpack('>d', data_bytes)[0]

def create_database():
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

def create_initial_json_file():
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

def get_sensor_name_by_can_id(can_id):
    # Mapeamos los IDs de sensores a los nombres de los sensores
    sensor_map = {
        16777216: "SOC",
        16777217: "BatPowerLosses",
        16777218: "BatteryVoltage",
        16777219: "BatteryPower",
        16777220: "BatteryCurrent",
        33554432: "MotorPowerOut",
        33554433: "MotorPowerIn",
        33554434: "MotorPowerLosses",
        33554435: "MotorNetTorque",
        50331648: "DrivelinePowerLoss",
        50331649: "MotorSpeed",
        50331650: "NetTractiveForce",
        67108864: "VehicleSpeed"
    }
    return sensor_map.get(can_id, "Unknown")


def save_to_mongo(can_id, sensor_name, timestamp, value):
    document = {
        "can_id": can_id,
        "sensor_name": sensor_name,
        "timestamp": timestamp,  # Guardar como objeto datetime
        "value": value
    }
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
    try:
        db[collection_name].insert_one(document)
        print(f"Guardado en MongoDB: {collection_name}, Documento: {document}")
    except Exception as e:
        print(f"Error al guardar en MongoDB: {e}")


def save_to_json(can_id, timestamp, value):
    if os.path.exists('received_data.json'):
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
        for sensor in existing_data["VehicleData"][system_name]:
            if sensor["can_id"] == str(can_id):
                sensor["timestamp"] = timestamp.isoformat()
                sensor["value"] = value
                save_to_mongo(sensor["can_id"], sensor["sensor_name"], timestamp, value)
                break
    else:
        print(f"ID de CAN {can_id} no mapeado a ningún sistema")

    with open('received_data.json', 'w') as file:
        json.dump(existing_data, file, indent=4)

def save_to_sqlite(can_id, timestamp, value):
    conn = sqlite3.connect('vehicle_data.db')
    cursor = conn.cursor()
    sensor_name = get_sensor_name_by_can_id(can_id)
    cursor.execute('''
    INSERT INTO can_data (can_id, sensor_name, timestamp, value)
    VALUES (?, ?, ?, ?)
    ''', (str(can_id), sensor_name, timestamp.isoformat(), value))
    conn.commit()
    conn.close()

def receive_can_message():
    create_database()  # Asegurar que la base de datos esté creada
    sensor_data = defaultdict(lambda: {"value": None, "timestamp": None})

    try:
        bus = can.Bus(channel='can0', bustype='socketcan')
        print("Esperando mensajes CAN...")

        # Diccionario para mapear IDs de sensores y timestamps
        sensor_ids = [16777216, 16777217, 16777218, 16777219, 16777220,
                      33554432, 33554433, 33554434, 33554435,
                      50331648, 50331649, 50331650,
                      67108864]

        while True:
            message = bus.recv()
            if message and len(message.data) == 8:
                can_id = message.arbitration_id

                if can_id in sensor_ids:
                    # Recibir valor del sensor
                    value = convert_from_8_bytes_float(message.data)
                    sensor_data[can_id]["value"] = value
                    print(f"Recibido valor {value} para CAN ID {can_id}")
                elif can_id - 0x10 in sensor_ids:
                    # Recibir timestamp
                    timestamp = convert_from_8_bytes_float(message.data)
                    timestamp = datetime.fromtimestamp(timestamp)
                    sensor_id = can_id - 0x10
                    sensor_data[sensor_id]["timestamp"] = timestamp
                    print(f"Recibido timestamp {timestamp} para CAN ID {sensor_id}")

                if sensor_data[can_id]["value"] is not None and sensor_data[can_id]["timestamp"] is not None:
                    # Guardar en JSON, SQLite y MongoDB
                    save_to_json(can_id, sensor_data[can_id]["timestamp"], sensor_data[can_id]["value"])
                    save_to_sqlite(can_id, sensor_data[can_id]["timestamp"], sensor_data[can_id]["value"])
                    sensor_data.pop(can_id)

    except can.CanError as e:
        print(f"Error en la interfaz CAN: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    receive_can_message()

