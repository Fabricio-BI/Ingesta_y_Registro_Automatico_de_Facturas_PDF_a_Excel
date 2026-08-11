import logging
import glob
import os

from core.logger import setup_logger
from core.procesamiento import convertir_pdf_a_markdown, detectar_plantilla, extraer_datos
from core.validador import validar_datos
from core.exportador_excel import exportar_a_excel
from core.extractor_ia import extraer_con_ia


setup_logger()
logger = logging.getLogger(__name__)

CARPETA_ENTRADA = "facturas_pdf"
ARCHIVO_SALIDA = "salida/facturas_extraidas.xlsx"


def procesar_factura(ruta_pdf: str) -> dict:
    """
    Procesa una sola factura PDF y devuelve su resultado como diccionario,
    listo para exportar a Excel.
    """
    nombre_archivo = os.path.basename(ruta_pdf)
    texto_markdown = convertir_pdf_a_markdown(ruta_pdf)
    plantilla = detectar_plantilla(texto_markdown)

    if plantilla is None:
        # Ningún proveedor conocido reconoce esta factura, probar con IA.
        logger.warning(f"sin plantilla, probando con IA ")
        datos = extraer_con_ia(texto_markdown)
        if datos is None:
            return {
                "estado": "sin plantilla",
                "errores": f"No se reconoció el proveedor de '{nombre_archivo}' "
                           f"y la IA no pudo procesarla (revisar GEMINI_API_KEY).",
            }
        datos["plantilla_usada"] = "ia_gemini"
    else:
        datos = extraer_datos(texto_markdown, plantilla)

    es_valida, errores = validar_datos(datos)

    datos["estado"] = "válida" if es_valida else "revisión manual"
    datos["errores"] = "; ".join(errores)
    return datos


def main():
    logger.info("INICIANDO PROCESO DE EXTRACCIÓN PDF A EXCEL")
    rutas_pdf = sorted(glob.glob(os.path.join(CARPETA_ENTRADA, "*.pdf")))

    if not rutas_pdf:
        logger.warning(f"No se encontraron PDFs en '{CARPETA_ENTRADA}/'.")
        return

    resultados = []
    for ruta_pdf in rutas_pdf:
        logger.info(f"Procesando: {ruta_pdf}")
        try:
            resultado = procesar_factura(ruta_pdf)
            resultados.append(resultado)

            estado = resultado.get("estado")
            if estado == "válida":
                logger.info(f"  -> estado: {estado}")
            else:
                logger.warning(f"  -> estado: {estado}")
        except Exception as e:
            nombre_archivo = os.path.basename(ruta_pdf)
            logger.error(f"  -> ERROR CRÍTICO al procesar '{nombre_archivo}': {e}")
            resultados.append({
                "proveedor": "Desconocido",
                "numero_factura": nombre_archivo,
                "estado": "error de lectura",
                "errores": f"El PDF está dañado o es ilegible: {str(e)}",
                "plantilla_usada": "ninguna"
            })

    os.makedirs(os.path.dirname(ARCHIVO_SALIDA), exist_ok=True)
    exportar_a_excel(resultados, ARCHIVO_SALIDA)
    logger.info(f"Listo. Resultados guardados en: {ARCHIVO_SALIDA}")
    logger.info("PROCESO COMPLETADO EXITOSAMENTE ")


if __name__ == "__main__":
    main()
