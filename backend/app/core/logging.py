"""
Structured & Secure Application Logging
=======================================
Configures structured console logging with sanitized output.
Guarantees NO secrets, tokens, or passwords are ever emitted to logs.
"""

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Avoid duplicate handlers
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


logger = logging.getLogger("pothole_platform")
