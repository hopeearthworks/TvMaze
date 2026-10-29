"""Logging layer (Module 8): writes activity and errors to automation.log."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
MAX_LOG_BYTES = 1_000_000  # Start a new file after ~1 MB...
LOG_BACKUP_COUNT = 5  # ...and keep automation.log.1 to automation.log.5.


def setup_logging(log_file: Path | str) -> logging.Logger:
    """Log INFO and above to a rotating log file, and warnings/errors to the console."""
    logger = logging.getLogger("tvmaze")
    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=MAX_LOG_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
