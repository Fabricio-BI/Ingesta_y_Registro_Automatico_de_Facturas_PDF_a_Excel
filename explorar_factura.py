"""
Script de EXPLORACIÓN — no forma parte del pipeline principal.
"""

import glob
import os
from core.procesamiento import convertir_pdf_a_markdown

CARPETA_ENTRADA = "facturas_pdf"

def main():
    rutas_pdf = sorted(glob.glob(os.path.join(CARPETA_ENTRADA, "*.pdf")))

    if not rutas_pdf:
        print(f"No se encontraron PDFs en '{CARPETA_ENTRADA}/'.")
        return

    for ruta_pdf in rutas_pdf:
        print("=" * 70)
        print(f"ARCHIVO: {ruta_pdf}")
        print("=" * 70)
        texto = convertir_pdf_a_markdown(ruta_pdf)
        print(texto)
        print()


if __name__ == "__main__":
    main()