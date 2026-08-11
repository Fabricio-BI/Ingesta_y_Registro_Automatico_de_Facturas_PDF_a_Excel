
from plantillas.esquema import Plantilla
 
PLANTILLA_BANCO_CORDILLERA = Plantilla(
    id="banco_cordillera",
    nombre_proveedor="Banco Cordillera",
    identificador_regex=r"Banco Cordillera",
    patrones={
        "ruc_proveedor": r"R\.U\.C\.:\s*(\d+)",
        "proveedor": r"(.*?)\nR\.U\.C\.:",
        "numero_factura": r"No\.\s+(\d{3}-\d{3}-\d+)",
        "fecha_emision": r"Fecha Emisión:\s*(\d{2}/\d{2}/\d{4})",
        "numero_autorizacion": r"CLAVE DE ACCESO\s*\n(\d+)",
        "descripcion": r"\d{6}\s+\d+\.\d{2}\s+([A-ZÁÉÍÓÚÑ ]+?)\s+\d+\.\d{2}\s+\d+\.\d{2}\s+\d+\.\d{2}",
        "base_imponible": r"SUBTOTAL 15%[ |]*?([\d.,]+)",
        "tarifa_iva": r"IVA\s+(\d+)%",
        "monto_iva": r"IVA \d+%[ |]*?([\d.,]+)",
        "total": r"VALOR TOTAL[ |]*?([\d.,]+)",
    },
)

PLANTILLA_BANCO_PRODUCTIVO_NACIONAL = Plantilla(
    id="banco_productivo_nacional",
    nombre_proveedor="Banco Productivo Nacional",
    identificador_regex=r"Banco Productivo Nacional",
    patrones={
        "ruc_proveedor": r"R\.U\.C\.:\s*(\d+)",
        "proveedor": r"FACTURA\n(.*?)\n",
        # Campo combinado: Establecimiento + Punto Emisión + Secuencial,
        # tres celdas separadas en la tabla del original -> se unen con
        # guion gracias al ajuste que hicimos en motor_extraccion.py.
        "numero_factura": r"\|\s*(\d{3})\s*\|\s*(\d{3})\s*\|\s*(\d+)\s*\|\s*\d{2}/\d{2}/\d{4}",
        "fecha_emision": r"\|\s*\d{3}\s*\|\s*\d{3}\s*\|\s*\d+\s*\|\s*(\d{2}/\d{2}/\d{4})",
        "numero_autorizacion": r"Número de autorización:\s*(\d+)",
        "descripcion": r"Descripción:\s*(.*?)\n",
        "base_imponible": r"Base Imponible[ |]*?([\d.,]+)",
        "tarifa_iva": r"Tarifa IVA[ |]*?(\d+)%",
        "monto_iva": r"Monto IVA[ |]*?([\d.,]+)",
        "total": r"TOTAL[ |]*?([\d.,]+)",
    },
)


PLANTILLA_BANCO_SOLIDARIDAD_ANDINA = Plantilla(
    id="banco_solidaridad_andina",
    nombre_proveedor="Banco Solidaridad Andina",
    identificador_regex=r"Banco Solidaridad Andina",
    patrones={
        "ruc_proveedor": r"RUC:\s*(\d+)",
        "proveedor": r"\|\s*(.*?)\s*\|.*?RUC:",
        "numero_factura": r"FACTURA No:\s*(\d{3}-\d{3}-\d+)",
        "fecha_emision": r"Fecha Emisión:\s*(\d{2}/\d{2}/\d{4})",
        "numero_autorizacion": r"CLAVE DE ACCESO\s*\n(\d+)",
        "descripcion": r"SVC001\s*\|\s*([A-ZÁÉÍÓÚÑ ]+?)\s*\|",
        "base_imponible": r"SUBTOTAL 15%[ |]*?([\d.,]+)",
        "tarifa_iva": r"IVA\s*(\d+)%",
        "monto_iva": r"IVA\s*\d+%[ |]*?([\d.,]+)",
        "total": r"VALOR TOTAL[ |]*?([\d.,]+)",
    },
)

# Plantilla Tarjeta Cumbre 
# Familia "Tarjeta Cumbre" -- Zenith, Prisma, Nortis y Elite Pay comparten
# el mismo formato de factura, por eso los patrones se definen una sola vez.

PATRONES_TARJETA_CUMBRE = {
    "ruc_proveedor": r"RUC:\s*(\d+)",
    "proveedor": r"\|\s*(.*?)\s*\|.*?RUC:",
    "numero_factura": r"FACTURA No:\s*(\d{3}-\d{3}-\d+)",
    "fecha_emision": r"Fecha Emisión:\s*(\d{2}/\d{2}/\d{4})",
    "numero_autorizacion": r"Clave de Acceso\s*\n(\d+)",
    "descripcion": r"\d{6}\s+\d+\.\d{2}\s+([A-ZÁÉÍÓÚÑ ]+?)\s+\d+\.\d{2}\s+\d+\.\d{2}",
    "base_imponible": r"Subtotal 15%[ |]*?([\d.,]+)",
    "tarifa_iva": r"IVA\s+(\d+)%",
    "monto_iva": r"IVA \d+%[ |]*?([\d.,]+)",
    "total": r"VALOR TOTAL[ |]*?([\d.,]+)",
}

PLANTILLA_TARJETA_CUMBRE_ZENITH = Plantilla(
    id="tarjeta_cumbre_zenith",
    nombre_proveedor="Tarjeta Cumbre Zenith",
    identificador_regex=r"Tarjeta Cumbre Zenith",
    patrones=PATRONES_TARJETA_CUMBRE,
)

PLANTILLA_TARJETA_CUMBRE_PRISMA = Plantilla(
    id="tarjeta_cumbre_prisma",
    nombre_proveedor="Tarjeta Cumbre Prisma",
    identificador_regex=r"Tarjeta Cumbre Prisma",
    patrones=PATRONES_TARJETA_CUMBRE,
)

PLANTILLA_TARJETA_CUMBRE_NORTIS = Plantilla(
    id="tarjeta_cumbre_nortis",
    nombre_proveedor="Tarjeta Cumbre Nortis",
    identificador_regex=r"Tarjeta Cumbre Nortis",
    patrones=PATRONES_TARJETA_CUMBRE,
)

PLANTILLA_TARJETA_CUMBRE_ELITE_PAY = Plantilla(
    id="tarjeta_cumbre_elite_pay",
    nombre_proveedor="Tarjeta Cumbre Elite Pay",
    identificador_regex=r"Tarjeta Cumbre Elite Pay",
    patrones=PATRONES_TARJETA_CUMBRE,
)