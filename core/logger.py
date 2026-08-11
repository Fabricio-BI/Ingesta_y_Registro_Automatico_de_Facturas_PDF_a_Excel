
import logging
import os
from logging.handlers import RotatingFileHandler

CARPETA_LOGS = "logs"
ARCHIVO_LOGS = os.path.join(CARPETA_LOGS, "procesamiento.log")


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # 1. Formato DETALLADO para el archivo físico (.log)
    formato_archivo = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    )
    formatter_archivo = logging.Formatter(
        formato_archivo, datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 2. Formato  para la consola
    formato_consola = "%(asctime)s | %(levelname)-7s | %(message)s"
    formatter_consola = logging.Formatter(formato_consola)

    # 3. Handler de Consola
    handler_consola = logging.StreamHandler()
    handler_consola.setFormatter(formatter_consola)
    logger.addHandler(handler_consola)

    # 4. Intentar crear carpeta y handler de archivo (con tolerancia a fallos de permisos)
    try:
        os.makedirs(CARPETA_LOGS, exist_ok=True)

        handler_archive = RotatingFileHandler(
            ARCHIVO_LOGS,
            maxBytes=10 * 1024 * 1024,  # 10 Megabytes
            backupCount=5,
            encoding="utf-8",
        )
        handler_archive.setFormatter(formatter_archivo)  # Usa el formato detallado
        logger.addHandler(handler_archive)
    except (OSError, PermissionError) as e:
        # Si falla por permisos de disco, advertimos y continuamos operando solo por consola
        logger.warning(
            f"No se pudo inicializar el archivo de logs en '{ARCHIVO_LOGS}' por problemas de permisos ({e}). "
            f"La aplicación continuará registrando únicamente por consola."
        )

    # 5. Silenciar logs ruidosos de dependencias de terceros (Clave para Producción)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)  # SDK de Gemini
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logger