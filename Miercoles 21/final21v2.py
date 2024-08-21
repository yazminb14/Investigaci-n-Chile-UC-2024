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


def convert_from_4_bytes_float(data_bytes):
    # Convertir 4 bytes en formato de punto flotante de 32 bits a un número decimal
    return struct.unpack('>f', data_bytes)[0]


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

    # Guardar el archivo JSON
    with open('received_data.json', 'w') as file:
        json.dump(data, file, indent=4)

    print("Archivo JSON inicial creado.")


def save_to_mongo(can_id, sensor_name, timestamp, value):
    # Guardar los datos en MongoDB como un objeto de tiempo `datetime`
    document = {
        "can_id": can_id,
        "sensor_name": sensor_name,
        "timestamp": timestamp,  # Aquí se guarda como un objeto `datetime`
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

    # Asegurarse de que la clave 'VehicleData' existe
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
                sensor["timestamp"] = timestamp.isoformat()  # Guardar como ISO format en el JSON
                sensor["value"] = decimal_value
                # Guardar en MongoDB como un objeto de tiempo `datetime`
                save_to_mongo(sensor["can_id"], sensor["sensor_name"], timestamp, decimal_value)
                found = True
                break
        if not found:
            print(f"No se encontró un sensor con el ID {can_id} en {system_name}")
    else:
        print(f"ID de CAN {can_id} no mapeado a ningún sistema")


def receive_can_message():
    create_database()  # Asegurar que la base de datos esté creada

    try:
        # Configurar la interfaz CAN
        bus = can.Bus(channel='can0', bustype='socketcan')
        print("Interfaz CAN configurada correctamente, esperando mensajes...")

        # Mantener un diccionario para almacenar los últimos valores de cada sensor
        last_sensor_data = {}

        while True:
            # Recibir mensaje
            message = bus.recv()
            if message:
                # Verificar si el mensaje tiene 8 bytes de datos (4 para timestamp y 4 para valor)
                if len(message.data) == 8:
                    # Desempaquetar el timestamp (float32) y el valor del sensor (float32)
                    timestamp = convert_from_4_bytes_float(message.data[:4])
                    decimal_value = convert_from_4_bytes_float(message.data[4:])

                    # Convertir el timestamp de epoch a un objeto datetime
                    timestamp = datetime.fromtimestamp(timestamp)

                    # Actualizar el último valor del sensor en el diccionario
                    last_sensor_data[message.arbitration_id] = (timestamp, decimal_value)

                    print(f"ID: {message.arbitration_id}, Timestamp: {timestamp}, Decimal Value: {decimal_value}, Extended: {message.is_extended_id}")

                    # Guardar el valor y el timestamp en el archivo JSON y MongoDB
                    save_to_json(message.arbitration_id, timestamp, decimal_value)
                else:
                    print(f"ID: {message.arbitration_id}, Data: {message.data}, Extended: {message.is_extended_id} (Datos no tienen 8 bytes)")

    except can.CanError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)


if __name__ == "__main__":
    receive_can_message()
