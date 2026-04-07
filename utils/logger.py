"""
Centralised logger for VIGIL-RQ.

Usage::

    from utils import get_logger
    log = get_logger(__name__)
    log.info("Hello from VIGIL-RQ")
"""

import logging
import logging.handlers
import sys

import config


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with rotating file and console handlers.

    Multiple calls with the same *name* always return the same Logger object,
    so handlers are added only once.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # already configured

    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler
    try:
        fh = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass  # running in a read-only environment – skip file logging

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger
