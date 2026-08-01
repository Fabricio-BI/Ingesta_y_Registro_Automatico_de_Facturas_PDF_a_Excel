
import glob
import os

from core.procesamiento import convertir_pdf_a_markdown, detectar_plantilla, extraer_datos
from core.validador import validar_datos
from core.exportador_excel import exportar_a_excel

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
        # Ningún proveedor conocido reconoce esta factura.
        # Aquí es donde, en el futuro, podrías conectar un fallback de IA.
        return {
            "estado": "sin plantilla",
            "errores": f"No se reconoció el proveedor de '{nombre_archivo}'. "
                       f"Crea una plantilla nueva en plantillas/.",
        }

    datos = extraer_datos(texto_markdown, plantilla)
    es_valida, errores = validar_datos(datos)

    datos["estado"] = "válida" if es_valida else "revisión manual"
    datos["errores"] = "; ".join(errores)
    return datos


def main():
    rutas_pdf = sorted(glob.glob(os.path.join(CARPETA_ENTRADA, "*.pdf")))

    if not rutas_pdf:
        print(f"No se encontraron PDFs en '{CARPETA_ENTRADA}/'.")
        return

    resultados = []
    for ruta_pdf in rutas_pdf:
        print(f"Procesando: {ruta_pdf}")
        resultado = procesar_factura(ruta_pdf)
        resultados.append(resultado)
        print(f"  -> estado: {resultado.get('estado')}")

    os.makedirs(os.path.dirname(ARCHIVO_SALIDA), exist_ok=True)
    exportar_a_excel(resultados, ARCHIVO_SALIDA)
    print(f"\nListo. Resultados guardados en: {ARCHIVO_SALIDA}")


if __name__ == "__main__":
    main()