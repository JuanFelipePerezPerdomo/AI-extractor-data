import os
import json
from openpyxl import Workbook, load_workbook


def obtener_ruta_excel():
    """Calcula y devuelve la ruta del escritorio con extensión .xlsx"""
    ruta_escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(ruta_escritorio, "registro_facturas.xlsx")


def guardar_en_excel(datos_factura):
    """Guarda el diccionario de datos en el Excel maestro."""
    ruta_excel = obtener_ruta_excel()

    # Convertimos la lista de iva a texto
    if 'lineas_iva' in datos_factura and isinstance(datos_factura['lineas_iva'], list):
        datos_factura['lineas_iva'] = json.dumps(datos_factura['lineas_iva'])

    # El orden exacto de nuestras columnas
    cabeceras = [
        "proveedor_emisor", "cliente_receptor", "numero_factura",
        "fecha", "total_base_imponible", "total_cuota_iva", "total", "lineas_iva"
    ]

    # Lógica de OpenPyXL para crear o añadir filas al Excel
    if not os.path.isfile(ruta_excel):
        # Si no existe, creamos un libro nuevo
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Facturas Extraidas"
        # Añadimos la fila de cabeceras
        hoja.append(cabeceras)
    else:
        # Si ya existe, lo cargamos en memoria
        libro = load_workbook(ruta_excel)
        hoja = libro.active

    # Preparamos los datos de la factura en el mismo orden que las cabeceras
    fila_datos = []
    for columna in cabeceras:
        # get() extrae el dato, y si no existe o es None, pone vacío ("")
        valor = datos_factura.get(columna, "")
        if valor is None:
            valor = ""
        fila_datos.append(valor)

    # Añadimos la fila al final del documento y guardamos
    hoja.append(fila_datos)
    libro.save(ruta_excel)

    return ruta_excel