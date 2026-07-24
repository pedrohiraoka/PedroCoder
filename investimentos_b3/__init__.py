"""
Módulo __init__ do pacote investimentos_b3.

Este pacote fornece uma aplicação completa para acompanhamento
de carteira de investimentos na bolsa brasileira (B3).
"""

__version__ = "1.0.0"
__author__ = "Investimentos B3 Team"
__description__ = "Acompanhamento de Carteira de Investimentos B3"

from data_fetcher import DataFetcher, DataFetcherError
from portfolio_manager import PortfolioManager, PortfolioManagerError, Asset, DividendRecord
from exporter import Exporter, ExporterError

__all__ = [
    'DataFetcher',
    'DataFetcherError',
    'PortfolioManager',
    'PortfolioManagerError',
    'Asset',
    'DividendRecord',
    'Exporter',
    'ExporterError',
]
