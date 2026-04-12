"""
Logging utilities for AstroLink.

Provides centralized logging configuration and retrieval functions
for consistent logging across all modules.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def get_logger(name: str = "astrolink") -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: Logger name (default: "astrolink")
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        # Set logger level from environment or default to INFO
        log_level = os.environ.get('ASTROLINK_LOG_LEVEL', 'INFO').upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    return logger


def setup_file_logging(log_dir: str = None) -> logging.FileHandler:
    """
    Setup file-based logging for persistent logs.
    
    Args:
        log_dir: Directory to store log files (default: ~/.astrolink/logs)
        
    Returns:
        File handler instance
    """
    if log_dir is None:
        log_dir = Path.home() / ".astrolink" / "logs"
    
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"astrolink_{timestamp}.log"
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Add to root logger
    logging.getLogger("astrolink").addHandler(file_handler)
    
    return file_handler


class ProcessingLog:
    """
    Context manager for tracking processing steps in a pipeline.
    
    Usage:
        with ProcessingLog(logger, "Reduction"):
            # processing code here
            pass
    """
    
    def __init__(self, logger: logging.Logger, step_name: str):
        """
        Initialize processing log context.
        
        Args:
            logger: Logger instance
            step_name: Name of the processing step
        """
        self.logger = logger
        self.step_name = step_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.step_name}...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            self.logger.info(f"Completed {self.step_name} in {duration:.2f}s")
        else:
            self.logger.error(f"Failed {self.step_name} after {duration:.2f}s: {exc_val}")
        return False  # Don't suppress exceptions
