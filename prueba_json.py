import can
import struct
import json

def convert_to_8_bytes_float(num):
    # Convertir el número decimal a un punto flotante de 64 bits en formato big-endian
    return struct.pack('>d', num)

def send_can_message(data_bytes):
    try:
        # Configurar la interfaz CAN
        bus = can.interface.Bus(channel='can0', bustype='socketcan')
        print("Interfaz CAN configurada correctamente")

        # Crear un mensaje CAN extendido (29 bits)
        msg_extended = can.Message(arbitration_id=0x1ABCDEF, 
                                   data=data_bytes, 
                                   is_extended_id=True)

        # Enviar el mensaje extendido
        try:
            bus.send(msg_extended)
            print(f"Mensaje extendido enviado correctamente: {data_bytes.hex().upper()}")
        except can.CanError as e:
            print("Error enviando el mensaje extendido:", e)

    except can.CanInterfaceNotImplementedError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)

def main():
    # Leer el archivo JSON
    with open('data.json', 'r') as file:
        data = json.load(file)

    # Obtener la lista de valores
    values = data.get("values", [])

    # Enviar cada valor por el bus CAN
    for value in values:
        if isinstance(value, (int, float)):
            data_bytes = convert_to_8_bytes_float(value)
            send_can_message(data_bytes)
        else:
            print(f"Valor no es numérico: {value}")

if __name__ == "__main__":
    main()
