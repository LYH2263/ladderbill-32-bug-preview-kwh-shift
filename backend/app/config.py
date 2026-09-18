import os
from pathlib import Path

APP_NAME = "Ladderbill"
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
DB_FILENAME = "app.db"
DEFAULT_PEAK_FACTOR = 1.2
