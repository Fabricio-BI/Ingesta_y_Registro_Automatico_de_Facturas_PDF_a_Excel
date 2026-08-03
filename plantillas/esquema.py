"""
Esquema base del proyecto  los 10
campos que se buscan en cualquier factura, sin importar el banco emisor.
El destino final es un Anexo Transaccional 
"""

from dataclasses import dataclass, field


# Los 10 campos que se buscan en cada factura. 

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
    
    """
    id: str
    nombre_proveedor: str
    identificador_regex: str
    patrones: dict[str, str]
    flags: dict[str, int] = field(default_factory=dict)
