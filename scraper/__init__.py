"""
Async Web Scraper Package

A modular, asynchronous, configurable, and scalable web scraping framework.
"""

from .config import ConfigError, ScraperConfig
from .parser import ParseError, parse_page, extract_data, extract_links
from .scraper import AsyncScraper, ScraperError
from .storage import DataStorage, StorageError

__version__ = '1.0.0'
__author__ = 'Web Scraper Team'
__all__ = [
    # Configuration
    'ScraperConfig',
    'ConfigError',
    
    # Parser
    'parse_page',
    'extract_data',
    'extract_links',
    'ParseError',
    
    # Scraper
    'AsyncScraper',
    'ScraperError',
    
    # Storage
    'DataStorage',
    'StorageError',
]
