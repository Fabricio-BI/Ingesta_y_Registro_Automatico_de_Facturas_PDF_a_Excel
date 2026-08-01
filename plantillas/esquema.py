"""
Esquema base del proyecto de conciliación bancaria (Anexo Transaccional).

Define el "contrato" de datos que toda plantilla debe respetar: los 10
campos que se buscan en cualquier factura, sin importar el banco emisor.

Este esquema reemplaza al del proyecto de práctica (facturas_extractor
original) porque el problema real que resolvemos es distinto: acá el
destino final es un Anexo Transaccional (formato fiscal ecuatoriano),
no una factura genérica.
"""

from dataclasses import dataclass, field


# Los 10 campos que se buscan en cada factura. Definidos junto con el
# usuario, a partir de un archivo real de conciliación (Anexo Marzo).
CAMPOS_FACTURA = [
    "ruc_proveedor",
    "proveedor",
    "numero_factura",
    "fecha_emision",
    "numero_autorizacion",
    "descripcion",
    "base_imponible",
    "tarifa_iva",
    "monto_iva",
    "total",
]

# Campos sin los cuales la factura no sirve para conciliación y se
# marca para revisión manual.
CAMPOS_OBLIGATORIOS = [
    "numero_factura",
    "fecha_emision",
    "numero_autorizacion",
    "base_imponible",
    "monto_iva",
    "total",
]


@dataclass
class Plantilla:
    """
    Reglas necesarias para extraer los 10 campos de un proveedor
    (banco) específico.

    Atributos:
        id: identificador corto y único (ej. "banco_productivo_nacional").
        nombre_proveedor: nombre legible del proveedor.
        identificador_regex: patrón que reconoce a este proveedor en el
            texto de la factura.
        patrones: diccionario campo -> regex, uno por cada dato a extraer.
        flags: flags de regex opcionales por campo (ej. re.DOTALL).
    """

    id: str
    nombre_proveedor: str
    identificador_regex: str
    patrones: dict[str, str]
    flags: dict[str, int] = field(default_factory=dict)
