"""
Logger - Structured logging configuration for the dashboard.

Provides consistent logging across all modules.
"""

import logging
import sys
from typing import Optional

import config


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__).
        level: Log level override (uses config.LOG_LEVEL by default).
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Set level
    log_level = getattr(logging, level or config.LOG_LEVEL, logging.INFO)
    logger.setLevel(log_level)
    
    # Avoid adding multiple handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(config.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


def setup_root_logger(level: Optional[str] = None):
    """
    Configure the root logger for the application.
    
    Args:
        level: Log level override.
    """
    log_level = getattr(logging, level or config.LOG_LEVEL, logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format=config.LOG_FORMAT,
        stream=sys.stdout
    )
    
    # Reduce verbosity for external libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('plotly').setLevel(logging.WARNING)
    logging.getLogger('dash').setLevel(logging.WARNING)
    logging.getLogger('flask').setLevel(logging.WARNING)


class LoggingContext:
    """Context manager for temporary log level changes."""
    
    def __init__(self, logger: logging.Logger, level: int):
        """
        Initialize logging context.
        
        Args:
            logger: Logger to modify.
            level: Temporary log level.
        """
        self.logger = logger
        self.level = level
        self.previous_level = logger.level
    
    def __enter__(self):
        """Enter context and set temporary level."""
        self.logger.setLevel(self.level)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore previous level."""
        self.logger.setLevel(self.previous_level)


# Module-level convenience functions
def debug(msg: str, name: str = "app"):
    """Log debug message."""
    logger = get_logger(name)
    logger.debug(msg)


def info(msg: str, name: str = "app"):
    """Log info message."""
    logger = get_logger(name)
    logger.info(msg)


def warning(msg: str, name: str = "app"):
    """Log warning message."""
    logger = get_logger(name)
    logger.warning(msg)


def error(msg: str, name: str = "app"):
    """Log error message."""
    logger = get_logger(name)
    logger.error(msg)


def critical(msg: str, name: str = "app"):
    """Log critical message."""
    logger = get_logger(name)
    logger.critical(msg)
