import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from python_json_logger import jsonlogger
from .config import settings

def setup_logging():
    """
    Configures the root logger for the application.
    - Logs to a rotating file in JSON format.
    - Logs to the console for local development.
    """
    # Ensure log directory exists
    log_dir = Path(settings.LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Use the logger provided by python-json-logger
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(levelname)s %(name)s %(message)s'
    )

    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=settings.LOG_ROTATION_MAX_BYTES,
        backupCount=settings.LOG_ROTATION_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)

    # Create console handler for clear, local development output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Get the root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # Clear existing handlers to avoid duplicates from uvicorn
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Prevent uvicorn's access logs from propagating to the root logger
    # to avoid duplicate log entries when running with uvicorn
    logging.getLogger("uvicorn.access").propagate = False
    
    logging.info("Logging configured successfully.")