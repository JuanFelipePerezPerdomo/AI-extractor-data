import csv
import json
import os


def obtener_ruta_csv():
    ruta_escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(ruta_escritorio, "registro_facturas.csv")


def guardar_en_csv(datos_factura):
    ruta_csv = obtener_ruta_csv()
    archivo_existe = os.path.isfile(ruta_csv)

    # Convertimos la lista de iva a texto
    if 'lineas_iva' in datos_factura and isinstance(datos_factura['lineas_iva'], list):
        datos_factura['lineas_iva'] = json.dumps(datos_factura['lineas_iva'])

    # cabeceras
    cabeceras = [
        "proveedor_emisor", "cliente_receptor", "numero_factura",
        "fecha", "total_base_imponible", "total_cuota_iva", "total", "lineas_iva"
    ]

    with open(ruta_csv, 'a', newline='', encoding='utf-8') as f:
        # extrasaction='ignore' es vital aquí por si Gemini devuelve algún campo que no esperamos
        writer = csv.DictWriter(f, fieldnames=cabeceras, extrasaction='ignore')

        if not archivo_existe:
            writer.writeheader()

        writer.writerow(datos_factura)

    return ruta_csv