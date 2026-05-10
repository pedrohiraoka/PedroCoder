"""Linux Terminal Assistant - Professional CLI/TUI for Linux administration."""

__version__ = "0.1.0"
__author__ = "LTA Team"

from lta.logger import setup_logger

logger = setup_logger(__name__)

__all__ = ["__version__", "logger"]
