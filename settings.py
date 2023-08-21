
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = "sqlite:///" + str(BASE_DIR) + "/sqlite.db"

PUBLISHING_INTERVAL = 30  # seconds