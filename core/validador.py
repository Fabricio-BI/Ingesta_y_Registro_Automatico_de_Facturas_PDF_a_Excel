"""
Validador de resultados de extracción.
Este es el componente que decide si el resultado de una plantilla es
confiable o no. Si algo falla , la factura se marca para revisión
manual. Si agregamos IA como alternativa de extraccion, este validador
disparara esa decisión (sin cambiar nada en el codigo).

"""

from datetime import datetime
import logging
from plantillas.esquema import CAMPOS_OBLIGATORIOS

logger = logging.getLogger(__name__)

TOLERANCIA_ARITMETICA = 0.05  # margen de error aceptado por redondeo


def normalizar_numero(valor: str) -> float | None:
    """
    Convierte un número en formato latino (punto = miles, coma = decimales,
    ej. "1.234,56") a float de Python.
    """
    if not valor:
        return None
    limpio = valor.strip().replace(".", "").replace(",", ".")
    try:
        return float(limpio)
    except ValueError:
        return None


def _fecha_valida(valor: str | None) -> bool:
    if not valor:
        return False
    try:
        datetime.strptime(valor, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def validar_datos(datos: dict) -> tuple[bool, list[str]]:
    """
    Valida un diccionario de datos extraídos.
    Returns:
        (es_valida, errores)
    """
    errores = []

    # 1. Completitud.
    for campo in CAMPOS_OBLIGATORIOS:
        if not datos.get(campo):
            errores.append(f"Falta el campo obligatorio: {campo}")

    if errores:
        logger.warning(
            f"Validación fallida (campos incompletos) para la factura del proveedor "
            f"'{datos.get('proveedor', 'Desconocido')}' (Plantilla: {datos.get('plantilla_usada', 'Ninguna')}). "
            f"Errores: {'; '.join(errores)}"
        )
        return False, errores

    # 2. Fecha con formato válido.
    if not _fecha_valida(datos.get("fecha_emision")):
        errores.append("Fecha de emisión con formato inválido o inexistente")

    # 3. Coherencia aritmética: Base Imponible + Monto IVA ≈ Total.
    base = normalizar_numero(datos.get("base_imponible"))
    iva = normalizar_numero(datos.get("monto_iva"))
    total = normalizar_numero(datos.get("total"))

    if base is None or iva is None or total is None:
        errores.append("Alguno de los montos (base_imponible, monto_iva, total) no es numérico")
    else:
        if abs((base + iva) - total) > TOLERANCIA_ARITMETICA:
            errores.append(
                f"Inconsistencia aritmética: {base} + {iva} != {total}"
            )

    if errores:
        logger.warning(
            f"Validación fallida para la factura del proveedor '{datos.get('proveedor', 'Desconocido')}' "
            f"(Plantilla: {datos.get('plantilla_usada', 'Ninguna')}). Errores: {'; '.join(errores)}"
        )
    else:
        logger.info(
            f"Validación exitosa para la factura del proveedor '{datos.get('proveedor')}' "
        )

    return (len(errores) == 0), errores


