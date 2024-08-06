import can

try:
    # Configurar la interfaz CAN
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
    print("Interfaz CAN configurada correctamente")

    # Crear un mensaje CAN extendido (29 bits)
    msg_extended = can.Message(arbitration_id=0x1ABCDEF, 
                               data=[0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88], 
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