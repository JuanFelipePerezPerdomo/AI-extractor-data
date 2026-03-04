import csv
import json
import os


def obtener_ruta_csv():
    ruta_escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(ruta_escritorio, "registro_facturas.csv")


def guardar_en_csv(datos_factura):
    ruta_csv = obtener_ruta_csv()

    # Comprobamos si el archivo no existe o si existe pero está vacío (0 bytes)
    es_nuevo = not os.path.isfile(ruta_csv) or os.path.getsize(ruta_csv) == 0

    if 'lineas_iva' in datos_factura and isinstance(datos_factura['lineas_iva'], list):
        datos_factura['lineas_iva'] = json.dumps(datos_factura['lineas_iva'])

    cabeceras = [
        "proveedor_emisor", "cliente_receptor", "numero_factura",
        "fecha", "total_base_imponible", "total_cuota_iva", "total", "lineas_iva"
    ]

    # utf-8-sig truco para que Excel lea las Ñ y acentos
    with open(ruta_csv, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=cabeceras, extrasaction='ignore')

        if es_nuevo:
            writer.writeheader()

        writer.writerow(datos_factura)

    return ruta_csv