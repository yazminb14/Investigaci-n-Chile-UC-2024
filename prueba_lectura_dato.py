import can

def receive_can_message():
    try:
        # Configurar la interfaz CAN
        bus = can.interface.Bus(channel='can0', bustype='socketcan')
        print("Interfaz CAN configurada correctamente, esperando mensajes...")

        while True:
            # Recibir mensaje
            message = bus.recv()
            if message:
                # Convertir los datos a formato hexadecimal
                data_hex = ' '.join(f'{byte:02X}' for byte in message.data)
                print(f"ID: {message.arbitration_id}, Data: {data_hex}, Extended: {message.is_extended_id}")

    except can.CanInterfaceNotImplementedError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)

if __name__ == "__main__":
    receive_can_message()
