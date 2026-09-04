import logging
from pathlib import Path

from core.exportador_excel import exportar_a_excel
from core.extractor_ia import extraer_con_ia
from core.procesamiento import (
    convertir_pdf_a_markdown,
    detectar_plantilla,
    extraer_datos,
)
from core.validador import validar_datos
from source.log_config import setup_logger
from source.paths import PROCESSED_DIR, RAW_DIR

setup_logger()
logger = logging.getLogger(__name__)

# Definimos el archivo de salida usando el Path procesado
ARCHIVO_SALIDA = PROCESSED_DIR / "facturas_extraidas.xlsx"


def procesar_factura(ruta_pdf: Path) -> dict:
    """
    Procesa una sola factura PDF y devuelve su resultado como diccionario,
    listo para exportar a Excel.
    """
    # Si viene como objeto Path, aseguramos extraer solo el nombre del archivo
    nombre_archivo = ruta_pdf

    texto_markdown = convertir_pdf_a_markdown(str(ruta_pdf))
    plantilla = detectar_plantilla(texto_markdown)

    if plantilla is None:
        # Ningún proveedor conocido reconoce esta factura, probar con IA.
        logger.warning("sin plantilla, probando con IA")
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
    rutas_pdf = sorted(RAW_DIR.glob("*.pdf"))

    if not rutas_pdf:
        logger.warning(f"No se encontraron PDFs en '{RAW_DIR}'.")
        return

    resultados = []
    for ruta_pdf in rutas_pdf:
        logger.info(f"Procesando: {ruta_pdf.name}")
        try:
            resultado = procesar_factura(ruta_pdf)
            resultados.append(resultado)

            estado = resultado.get("estado")
            if estado == "válida":
                logger.info(f"  -> estado: {estado}")
            else:
                logger.warning(f"  -> estado: {estado}")
        except Exception as e: # noqa: BLE001
            nombre_archivo = ruta_pdf.name
            logger.error(f"  -> ERROR CRÍTICO al procesar '{nombre_archivo}': {e}")
            resultados.append({
                "proveedor": "Desconocido",
                "numero_factura": nombre_archivo,
                "estado": "error de lectura",
                "errores": f"El PDF está dañado o es ilegible: {str(e)}",
                "plantilla_usada": "ninguna"
            })

    # Asegura que la carpeta processed exista antes de guardar
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    exportar_a_excel(resultados, ARCHIVO_SALIDA)
    logger.info(f"Listo. Resultados guardados en: {ARCHIVO_SALIDA}")
    logger.info("PROCESO COMPLETADO EXITOSAMENTE")


if __name__ == "__main__":
    main()
