import can
import struct

def convert_to_8_bytes(num):
    # Convertir el número a 8 bytes en formato big-endian
    return struct.pack('>Q', num)

def main():
    try:
        # Configurar la interfaz CAN
        bus = can.interface.Bus(channel='can0', bustype='socketcan')
        print("Interfaz CAN configurada correctamente")

        # Solicitar un número al usuario
        user_input = input("Ingrese un número: ")
        num = int(user_input)

        # Convertir el número a 8 bytes
        data_bytes = convert_to_8_bytes(num)

        # Crear un mensaje CAN extendido (29 bits)
        msg_extended = can.Message(arbitration_id=0x00BCDEF, 
                                   data=data_bytes, 
                                   is_extended_id=True)

        # Enviar el mensaje extendido
        try:
            bus.send(msg_extended)
            print("Mensaje extendido enviado correctamente")
        except can.CanError as e:
            print("Error enviando el mensaje extendido:", e)

    except can.CanInterfaceNotImplementedError as e:
        print("Error configurando la interfaz CAN:", e)
    except Exception as e:
        print("Otro error:", e)

if __name__ == "__main__":
    main()
