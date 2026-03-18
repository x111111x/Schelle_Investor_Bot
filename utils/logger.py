"""Logging configuration for Project Alpha."""

import logging
import os
from logging.handlers import RotatingFileHandler

from config import LOG_PATH


def get_logger(name: str) -> logging.Logger:
    """Return a logger with file + console handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    fh = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
