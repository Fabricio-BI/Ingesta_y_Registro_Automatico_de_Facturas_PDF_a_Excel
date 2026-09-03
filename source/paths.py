from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT/"data"/"raw"
PROCESSED_DIR = ROOT /"data"/"processed"
LOG_DIR = ROOT /"logs"
LOG_FILE = LOG_DIR/ "invoice_extraction.log"


LOG_DIR.mkdir(parents=True, exist_ok=True)