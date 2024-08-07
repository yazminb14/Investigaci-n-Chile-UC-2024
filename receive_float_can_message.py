import can
import struct

def convert_from_8_bytes_float(data_bytes):
    # Convertir 8 bytes en formato de punto flotante de 64 bits a un número decimal
    return struct.unpack('>d', data_bytes)[0]

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
                else:
                    print(f"ID: {message.arbitration_id}, Data: {message.data}, Extended: {message.is_extended_id} (Datos no tienen 8 bytes)")

    except can.CanInterfaceNotImplementedError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)

if __name__ == "__main__":
    receive_can_message()
