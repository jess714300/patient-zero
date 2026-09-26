"""Shared logging setup for Patient Zero."""

import logging
import sys

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: str = "INFO") -> None:
    """Set up stdout logging at application startup, replacing existing root handlers."""
    # Replace any existing root handlers so messages have one shared output.
    logging.basicConfig(
        level=level,
        format=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger by name. Use ``__name__`` to identify the calling module."""
    return logging.getLogger(name)
