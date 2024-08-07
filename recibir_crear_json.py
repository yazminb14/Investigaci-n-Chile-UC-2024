import can
import struct
import json
import os

def convert_from_8_bytes_float(data_bytes):
    # Convertir 8 bytes en formato de punto flotante de 64 bits a un número decimal
    return struct.unpack('>d', data_bytes)[0]

def save_to_json(data):
    # Leer datos existentes del archivo JSON
    if os.path.exists('received_data.json'):
        try:
            with open('received_data.json', 'r') as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            existing_data = {"values": []}
    else:
        existing_data = {"values": []}

    # Añadir el nuevo dato
    existing_data["values"].append(data)

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
                    save_to_json(decimal_value)
                else:
                    print(f"ID: {message.arbitration_id}, Data: {message.data}, Extended: {message.is_extended_id} (Datos no tienen 8 bytes)")

    except can.CanInterfaceNotImplementedError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)

if __name__ == "__main__":
    receive_can_message()
