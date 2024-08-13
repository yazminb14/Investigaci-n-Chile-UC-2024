from openpyxl import load_workbook

def print_column_values(file_path, sheet_name, column_letter):
    # Carga el archivo XLSX
    wb = load_workbook(file_path, data_only=True)
    
    # Selecciona la hoja de cálculo por nombre
    sheet = wb[sheet_name]
    
    # Imprime los valores de la columna especificada
    for row in sheet[column_letter]:
        print(row.value)

# Ejemplo de uso
file_path = '/home/yazminbc/Downloads/EVsimdata.xlsx'  # Reemplaza con la ruta a tu archivo
sheet_name = 'Hoja1'  # Reemplaza con el nombre de la hoja
column_letter = 'B'  # Reemplaza con la letra de la columna que quieres leer

print_column_values(file_path, sheet_name, column_letter)
