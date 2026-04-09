"""
MVP Crawler/Web Scraper - Pacote Principal

Este pacote implementa um crawler ético e modular para extração
de dados estruturados de páginas web.
"""

__version__ = "1.0.0"
__author__ = "Data Architecture Team"

from src.models import Company, Contact, Service, Price, CrawledPage
from src.crawler import Crawler, CrawlerConfig
from src.parser import Parser, ParseResult
from src.storage import Storage, StorageFormat
from src.utils import setup_logging, normalize_phone, normalize_email

__all__ = [
    "Company",
    "Contact", 
    "Service",
    "Price",
    "CrawledPage",
    "Crawler",
    "CrawlerConfig",
    "Parser",
    "ParseResult",
    "Storage",
    "StorageFormat",
    "setup_logging",
    "normalize_phone",
    "normalize_email",
]
