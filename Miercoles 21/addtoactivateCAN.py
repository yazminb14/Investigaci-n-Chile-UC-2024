import subprocess

def setup_can_interface():
    try:
        # Ejecutar comando para configurar la interfaz CAN con bitrate 500000
        subprocess.run(["sudo", "ip", "link", "set", "can0", "up", "type", "can", "bitrate", "500000"], check=True)
        
        # Ejecutar comando para subir la interfaz CAN
        subprocess.run(["sudo", "ifconfig", "can0", "up"], check=True)
        
        print("Interfaz CAN configurada correctamente")
    except subprocess.CalledProcessError as e:
        print(f"Error al configurar la interfaz CAN: {e}")

