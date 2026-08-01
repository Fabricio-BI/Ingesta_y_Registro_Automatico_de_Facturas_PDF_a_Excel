import re
from markitdown import MarkItDown
from plantillas.esquema import CAMPOS_FACTURA, Plantilla
from plantillas.registro import PLANTILLAS_REGISTRADAS



# Funcion de conversion de PDF a Markdown

_md = MarkItDown()


def convertir_pdf_a_markdown(ruta_pdf: str) -> str:
    """
    Convierte un PDF a texto Markdown.

    Args:
        ruta_pdf: ruta al archivo PDF de la factura.

    Returns:
        Texto en formato Markdown (tablas incluidas como | col | col |).
    """
    resultado = _md.convert(ruta_pdf)
    return resultado.text_content



# Funcion de deteccion de plantilla  .
def detectar_plantilla(texto_markdown: str) -> Plantilla | None:
    """Busca, en orden, la primera plantilla registrada cuyo identificador coincida con el texto de la factura """
    for plantilla in PLANTILLAS_REGISTRADAS:
        if re.search(plantilla.identificador_regex, texto_markdown):
            return plantilla
    return None



# Funcion de extraccion : Aplicar los patrones de una Plantilla sobre un texto y devuelve un diccionario de campos.
def extraer_datos(texto_markdown: str, plantilla: Plantilla) -> dict:
    """ Aplica los patrones de una plantilla sobre el texto de la factura """
    datos = {campo: None for campo in CAMPOS_FACTURA}
    datos["proveedor"] = plantilla.nombre_proveedor
    datos["plantilla_usada"] = plantilla.id

    for campo, patron in plantilla.patrones.items():
        flags = plantilla.flags.get(campo, 0)
        coincidencia = re.search(patron, texto_markdown, flags)
        if coincidencia:
            grupos = [g.strip() for g in coincidencia.groups() if g is not None]
            datos[campo] = "-".join(grupos)

    return datos