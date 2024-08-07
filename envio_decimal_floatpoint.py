import can
import struct

def convert_to_8_bytes_float(num):
    # Convertir el número decimal a un punto flotante de 64 bits en formato big-endian
    return struct.pack('>d', num)

def main():
    try:
        # Configurar la interfaz CAN
        bus = can.interface.Bus(channel='can0', bustype='socketcan')
        print("Interfaz CAN configurada correctamente")

        # Solicitar un número decimal al usuario
        user_input = float(input("Ingrese un número decimal: "))

        # Convertir el número a 8 bytes en formato de punto flotante de 64 bits
        data_bytes = convert_to_8_bytes_float(user_input)
        
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
    except ValueError:
        print("Por favor, ingrese un número decimal válido.")
    except Exception as e:
        print("Otro error:", e)

if __name__ == "__main__":
    main()
