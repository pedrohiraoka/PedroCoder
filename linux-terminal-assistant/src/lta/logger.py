"""Centralized logging configuration for LTA.

Provides structured logging with console and file handlers,
supporting multiple log levels and formatted output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    use_colors: bool = True,
) -> logging.Logger:
    """Set up and return a configured logger instance.

    Args:
        name: Logger name (typically __name__).
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file for persistent logging.
        use_colors: Whether to use colored output in console.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = ColoredFormatter if use_colors else PlainFormatter

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter())
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(PlainFormatter())
        logger.addHandler(file_handler)

    return logger


class PlainFormatter(logging.Formatter):
    """Plain text log formatter without colors."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output."""

    COLORS = {
        logging.DEBUG: "\x1b[36m",      # Cyan
        logging.INFO: "\x1b[32m",       # Green
        logging.WARNING: "\x1b[33m",    # Yellow
        logging.ERROR: "\x1b[31m",      # Red
        logging.CRITICAL: "\x1b[35m",   # Magenta
    }
    RESET = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        record.msg = f"{color}{record.msg}{self.RESET}" if record.levelno >= logging.WARNING else record.msg
        return super().format(record)


def get_log_level_from_string(level_str: str) -> int:
    """Convert string log level to logging constant.

    Args:
        level_str: Log level string (debug, info, warning, error, critical).

    Returns:
        Corresponding logging level constant.
    """
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    return level_map.get(level_str.lower(), logging.INFO)
