"""
Show logs in the terminal and optionally save them to a JSON file.
Set up logging once when the program starts.
"""

import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar
from uuid import uuid4

from colorama import Back, Fore, Style, just_fix_windows_console
from pythonjsonlogger.json import JsonFormatter

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ColorFormatter(logging.Formatter):
    """
    Color terminal messages by log level without changing the original message.
    """

    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.WHITE + Back.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Add color to the message and reset the terminal color afterward.
        """
        message = super().format(record)
        color = self.COLORS.get(record.levelno, "")
        return f"{color}{message}{Style.RESET_ALL}" if color else message


def _resolve_level(value: str) -> int:
    """
    Convert a level name, such as INFO or debug, to its logging number.
    """
    level = logging.getLevelNamesMapping().get(value.upper())
    if level is None:
        raise ValueError(f"Unknown logging level: {value}")
    return level


def _create_console_handler(level: int) -> logging.StreamHandler:
    """
    Write logs to standard output, with color when it is a terminal.
    """
    just_fix_windows_console()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    formatter = ColorFormatter if use_color else logging.Formatter
    handler.setFormatter(formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT))
    return handler


def _create_file_handler(directory: Path, level: int) -> logging.FileHandler:
    """
    Create a new JSON log file with code locations and an ID for this run.
    """
    directory.mkdir(parents=True, exist_ok=True)
    run_id = uuid4().hex
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    path = directory / f"patient_zero_{timestamp}_{run_id}.log"
    handler = logging.FileHandler(path, mode="x", encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(
        JsonFormatter(
            "%(name)s %(levelname)s %(filename)s %(lineno)s %(message)s",
            timestamp=True,
            static_fields={"run_id": run_id},
        )
    )
    return handler


def configure_logging(
    level: str | None = None,
    *,
    log_dir: Path | None = None,
    file_level: str | None = None,
) -> Path | None:
    """
    Set up terminal logs and optional JSON file logs.
    Arguments take priority over environment variables.
    Return the log file path, or None if logs are only shown in the terminal.
    """
    console_level = _resolve_level(level if level is not None else os.environ.get("P0_LOG_LEVEL", "INFO"))
    directory_setting = os.environ.get("P0_LOG_DIR")
    if log_dir is None and directory_setting:
        log_dir = Path(directory_setting)

    json_level = None
    if log_dir is not None:
        json_level = _resolve_level(file_level if file_level is not None else os.environ.get("P0_FILE_LOG_LEVEL", "DEBUG"))

    handlers: list[logging.Handler] = [_create_console_handler(console_level)]
    log_path = None
    if log_dir is not None and json_level is not None:
        file_handler = _create_file_handler(log_dir, json_level)
        handlers.append(file_handler)
        log_path = Path(file_handler.baseFilename)

    # Root filtering must allow messages intended for either output.
    logging.basicConfig(level=min(handler.level for handler in handlers), handlers=handlers, force=True)
    return log_path


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name. Leave output settings unchanged.
    """
    return logging.getLogger(name)
