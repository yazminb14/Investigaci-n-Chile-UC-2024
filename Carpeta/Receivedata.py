import can
import struct
import json
import os
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
    try:
        # Configurar la interfaz CAN
        bus = can.interface.Bus(channel='can0', bustype='socketcan')
        print("Interfaz CAN configurada correctamente, esperando mensajes...")

        while True:
            # Recibir mensaje
            message = bus.recv()
            if message:
                # Verificar si el mensaje tiene 8 bytes de datos
                if len(message.data) == 8:
                    # Convertir los datos a punto flotante de 64 bits
                    decimal_value = convert_from_8_bytes_float(message.data)
                    print(f"ID: {message.arbitration_id}, Decimal Value: {decimal_value}, Extended: {message.is_extended_id}")

                    # Guardar el valor decimal en el archivo JSON
                    save_to_json(message.arbitration_id, decimal_value)
                else:
                    print(f"ID: {message.arbitration_id}, Data: {message.data}, Extended: {message.is_extended_id} (Datos no tienen 8 bytes)")

    except can.CanInterfaceNotImplementedError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)

if __name__ == "__main__":
    receive_can_message()

