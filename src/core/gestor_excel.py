import os
import json
from openpyxl import Workbook, load_workbook


def obtener_ruta_excel():
    ruta_escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(ruta_escritorio, "registro_facturas.xlsx")


def guardar_en_excel(datos_factura):
    ruta_excel = obtener_ruta_excel()

    if 'lineas_iva' in datos_factura and isinstance(datos_factura['lineas_iva'], list):
        datos_factura['lineas_iva'] = json.dumps(datos_factura['lineas_iva'])

    # NUEVO: Hemos añadido "nombre_documento" al principio de la lista
    cabeceras = [
        "nombre_documento", "proveedor_emisor", "cliente_receptor", "numero_factura",
        "fecha", "total_base_imponible", "total_cuota_iva", "total", "lineas_iva"
    ]

    if not os.path.isfile(ruta_excel):
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Facturas Extraidas"
        hoja.append(cabeceras)
    else:
        libro = load_workbook(ruta_excel)
        hoja = libro.active

    fila_datos = []
    for columna in cabeceras:
        valor = datos_factura.get(columna, "")
        if valor is None:
            valor = ""
        fila_datos.append(valor)

    hoja.append(fila_datos)
    libro.save(ruta_excel)

    return ruta_excel