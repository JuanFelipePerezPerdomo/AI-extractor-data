import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Cargamos las variables de entorno
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


def obtener_cliente():
    """Verifica la API Key y devuelve el cliente de Gemini."""
    if not API_KEY:
        raise ValueError("No se encontró la API Key en el archivo .env.")
    return genai.Client(api_key=API_KEY)


def extraer_datos_factura(ruta_archivo):
    """Sube el archivo, extrae los datos y los devuelve como diccionario."""
    client = obtener_cliente()
    archivo_subido = None

    try:
        archivo_subido = client.files.upload(file=ruta_archivo)

        prompt_predefinido = """
        Eres un sistema experto en extracción estructurada de datos de facturas españolas.
        TAREA: Extraer la información de la factura de compra proporcionada y devolver EXCLUSIVAMENTE un objeto JSON válido.
        REGLAS ESTRICTAS:
        1. Devuelve SOLO JSON válido. Sin texto adicional, explicaciones ni bloques de código.
        2. El JSON debe comenzar con { y terminar con }.
        3. No devuelvas una lista. Devuelve un único objeto JSON.
        4. Si un campo no está presente, usa null.
        5. Fecha en formato YYYY-MM-DD. Importes numéricos usan punto (.) como decimal sin moneda.
        6. "total" debe incluir importe y moneda ej: "123.45 EUR".
        7. Si usa IGIC (Canarias), trátalo como IVA.
        8. Si hay múltiples tipos impositivos, inclúyelos en "lineas_iva". Si no hay, usa [].

        ESTRUCTURA OBLIGATORIA:
        {
        "proveedor_emisor": "Nombre de la empresa que vende/emite la factura. string | null",
        "cliente_receptor": "Nombre de la empresa que compra/recibe la factura. string | null",
        "numero_factura": string | null,
        "fecha": string | null,
        "total_base_imponible": number | null,
        "total_cuota_iva": number | null,
         "total": string | null,
         "lineas_iva": [{"base": number, "porcentaje": number, "cuota": number}]
        }
        """

        respuesta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[archivo_subido, prompt_predefinido],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )

        datos_json = json.loads(respuesta.text.strip())
        return datos_json

    except json.JSONDecodeError:
        raise ValueError("El modelo no devolvió un JSON válido con la estructura solicitada.")
    except Exception as e:
        raise e
    finally:
        # limpiamos el archivo del servidor de Google
        if archivo_subido:
            try:
                client.files.delete(name=archivo_subido.name)
            except Exception:
                pass
