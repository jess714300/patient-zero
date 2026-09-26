"""
Shared logging utilities for Patient Zero.

This module provides a consistent logging configuration across Patient Zero.
Services, ETLs, DAGs, and other application components should retrieve loggers
through ``get_logger`` rather than configuring Python loggers independently.

The implementation intentionally builds on Python's standard ``logging``
library rather than introducing a separate logging service. Python maintains
logger instances by name, giving Patient Zero shared logger behavior without
requiring additional lifecycle management in the service factory.
"""

import logging
import sys

DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(
        name: str,
        level: str = "INFO",
) -> logging.Logger:
    """
    Return a consistently configured logger for the given name and level.

    A stdout stream handler is added the first time a logger is configured for a given name.
    Existing handlers are preserved to prevent duplicatre terminal output when the same logger is retrieved multiple times.

    Args:
        name: The name of the logger to retrieve.
        level: The logging level to set for the logger. Defaults to "INFO".

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
