"""
Extractor de respaldo basado en IA (Google Gemini).

Se activa únicamente cuando ninguna plantilla de reglas reconoce el
proveedor de una factura -- ver el punto de enganche en main.py.

"""

import json
import os

from google import genai

from plantillas.esquema import CAMPOS_FACTURA

MODELO = "gemini-3.5-flash"

_DESCRIPCION_CAMPOS = {
    "ruc_proveedor": "RUC del proveedor emisor de la factura (solo dígitos)",
    "proveedor": "Nombre o razón social del proveedor emisor",
    "numero_factura": "Establecimiento-PuntoEmision-Secuencial, combinados con guion (ej: 001-002-000012345)",
    "fecha_emision": "Fecha de emisión de la factura, formato DD/MM/AAAA",
    "numero_autorizacion": "Número de autorización o clave de acceso (solo dígitos, puede ser largo)",
    "descripcion": "Descripción del servicio o producto principal facturado",
    "base_imponible": "Base imponible antes de IVA (formato numérico, coma o punto decimal tal como aparece)",
    "tarifa_iva": "Porcentaje de IVA aplicado, solo el número (ej: 15)",
    "monto_iva": "Monto de IVA en la moneda de la factura",
    "total": "Valor total de la factura",
}


def _construir_esquema_json():
    """Arma el response_schema que le pedimos a Gemini, a partir de
    CAMPOS_FACTURA -- si mañana se agrega un campo al esquema, este
    extractor lo pide automáticamente, sin tocar este archivo."""
    propiedades = {
        campo: {"type": "string", "description": _DESCRIPCION_CAMPOS.get(campo, "")}
        for campo in CAMPOS_FACTURA
    }
    return {
        "type": "object",
        "properties": propiedades,
        "required": CAMPOS_FACTURA,
    }


def extraer_con_ia(texto_markdown: str) -> dict | None:
    """
    Extrae los CAMPOS_FACTURA de una factura usando Gemini, como
    respaldo cuando ninguna plantilla de reglas la reconoció.

    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("  [IA] Falta la variable de entorno GEMINI_API_KEY.")
        return None

    cliente = genai.Client(api_key=api_key)

    prompt = (
        "Actúa como un extractor de datos contables experto en documentos del SRI de Ecuador.\n"
        "Tu tarea es extraer datos de la factura ecuatoriana provista en formato Markdown.\n\n"
        
        "REGLAS DE EXTRACCIÓN Y FORMATEO ESTRICTAS:\n"
        "1. No inventes datos. Si un campo no existe en el documento, devuélvelo como un string vacío.\n"
        "2. NÚMERO DE FACTURA: Debe tener siempre el formato 'XXX-XXX-XXXXXXXXX' (ej: 001-010-000045123). "
           "Si en el texto el establecimiento, punto de emisión y secuencial están separados, únelos con guiones "
           "y completa con ceros a la izquierda si es necesario.\n"
        "3. NÚMERO DE AUTORIZACIÓN: Corresponde a la 'Clave de Acceso' o 'Número de Autorización' (un número largo de 49 dígitos). "
           "Extrae solo los dígitos, sin espacios ni saltos de línea.\n"
        "4. FECHAS: Devuelve la fecha de emisión siempre en formato 'DD/MM/AAAA' (ej: 15/08/2025). "
           "Si viene en otro formato o con nombres de meses en texto, conviértela.\n"
        "5. RUC PROVEEDOR: Extrae únicamente los 13 dígitos numéricos.\n"
        "6. VALORES NUMÉRICOS (Base, IVA, Total): Extrae solo el número. Mantén la coma o punto decimal que use el documento original.\n\n"
        
        f"--- TEXTO DE LA FACTURA ---\n{texto_markdown}"
        
    )

    try:
        respuesta = cliente.models.generate_content(
            model=MODELO,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": _construir_esquema_json(),
            },
        )
        datos = json.loads(respuesta.text)
        return datos
    except Exception as error:
        print(f"  [IA] Error al llamar a la API: {error}")
        return None



