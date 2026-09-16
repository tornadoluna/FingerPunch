from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from types import TracebackType

from fingerpunch.paths import app_data_dir

LOGGER_NAME = "fingerpunch"
LOG_FILENAME = "fingerpunch.log"
MAX_LOG_BYTES = 512 * 1024
BACKUP_COUNT = 3
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def log_file_path() -> Path:
    return app_data_dir() / LOG_FILENAME


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    try:
        path = log_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logger.warning("Could not open a log file; logging to stderr only", exc_info=True)

    return logger


def install_excepthook() -> None:
    previous = sys.excepthook

    def handle(
        exc_type: type[BaseException],
        value: BaseException,
        traceback: TracebackType | None,
    ) -> None:
        logging.getLogger(LOGGER_NAME).critical(
            "Unhandled exception", exc_info=(exc_type, value, traceback)
        )
        previous(exc_type, value, traceback)

    sys.excepthook = handle
