import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_FILE = "pipeline.log"
logs_path = os.path.join(os.getcwd(), "logs")
os.makedirs(logs_path, exist_ok=True)

LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

file_handler = RotatingFileHandler(
    LOG_FILE_PATH,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)

logging.basicConfig(
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        file_handler,
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("winequalitypredictionlogger")
