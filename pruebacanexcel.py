import time
import struct
import can
from openpyxl import load_workbook

def send_float64_over_can(bus, message_id, value):
    # Convierte el valor float a 64-bit (double precision) en formato bytes
    packed_value = struct.pack('>d', value)  # '>d' para big-endian double
    
    # Crea el mensaje CAN
    message = can.Message(
        arbitration_id=message_id,
        data=packed_value,
        is_extended_id=False
    )
    
    # Envía el mensaje
    bus.send(message)

def read_column_values(file_path, sheet_name, column_letter):
    # Carga el archivo XLSX
    wb = load_workbook(file_path, data_only=True)
    sheet = wb[sheet_name]
    
    # Lee los valores de la columna especificada
    values = []
    for row in sheet[column_letter]:
        if isinstance(row.value, float):
            values.append(row.value)
    return values

def main():
    # Configura la interfaz CAN
    bus = can.interface.Bus(channel='can0', bustype='socketcan')  # Ajusta según tu configuración

    # Parámetros del archivo y columna
    file_path = '/home/yazminbc/Downloads/EVsimdata.xlsx'  # Reemplaza con la ruta a tu archivo
    sheet_name = 'Hoja1'  # Reemplaza con el nombre de la hoja
    column_letter = 'F'
    message_id = 0x123  # Identificador del mensaje CAN, ajusta según tus necesidades

    # Lee los valores de la columna
    values = read_column_values(file_path, sheet_name, column_letter)

    # Envía los valores por CAN a 2Hz
    for value in values:
        send_float64_over_can(bus, message_id, value)
        time.sleep(0.5)  # Espera 0.5 segundos para mantener una frecuencia de 2Hz

if __name__ == "__main__":
    main()
