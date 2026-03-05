import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "tariff_db"),
    "user": os.getenv("DB_USER", "tariff_user"),
    "password": os.getenv("DB_PASSWORD", ""),
}

STORAGE_CONFIG = {
    "type": "local",  # or "s3"
    "local_path": RAW_DATA_DIR,
    "html_dir": RAW_DATA_DIR / "html",
    "pdf_dir": RAW_DATA_DIR / "pdf",
    "json_dir": RAW_DATA_DIR / "json",
}

PARSER_VERSION = "1.0.0"

SOURCE_PRIORITIES = {
    "federal_register": 1,
    "cbp_csms": 2,
    "ustr": 3,
}
