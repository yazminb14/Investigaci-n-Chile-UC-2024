import can
import struct
import sqlite3
from datetime import datetime

def convert_from_8_bytes_float(data_bytes):
    return struct.unpack('>d', data_bytes)[0]

def save_to_db(can_id, decimal_value):
    conn = sqlite3.connect('vehicle_data.db')
    cursor = conn.cursor()

    timestamp = datetime.utcnow().isoformat()

    systems = {
        "16777216": ("BatterySystem", "SOC"),
        "16777217": ("BatterySystem", "BatPowerLosses"),
        "16777218": ("BatterySystem", "BatteryVoltage"),
        "16777219": ("BatterySystem", "BatteryPower"),
        "16777220": ("BatterySystem", "BatteryCurrent"),
        "33554432": ("MotorSystem", "MotorPowerOut"),
        "33554433": ("MotorSystem", "MotorPowerIn"),
        "33554434": ("MotorSystem", "MotorPowerLosses"),
        "33554435": ("MotorSystem", "MotorNetTorque"),
        "50331648": ("DrivelineSystem", "DrivelinePowerLoss"),
        "50331649": ("DrivelineSystem", "MotorSpeed"),
        "50331650": ("DrivelineSystem", "NetTractiveForce"),
        "67108864": ("GliderSystem", "VehicleSpeed")
    }

    system_info = systems.get(str(can_id), None)
    if system_info:
        system_name, sensor_name = system_info
        cursor.execute(f'''
        INSERT INTO {system_name} (sensor_name, can_id, timestamp, value)
        VALUES (?, ?, ?, ?)
        ''', (sensor_name, can_id, timestamp, decimal_value))

    conn.commit()
    conn.close()

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

                    # Guardar el valor decimal en la base de datos
                    save_to_db(message.arbitration_id, decimal_value)
                else:
                    print(f"ID: {message.arbitration_id}, Data: {message.data}, Extended: {message.is_extended_id} (Datos no tienen 8 bytes)")

    except can.CanInterfaceNotImplementedError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)

if __name__ == "__main__":
    receive_can_message()

