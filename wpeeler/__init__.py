"""
WPeeler - Web Design DNA Extractor

Pacote de análise de DNA visual de websites.
"""

from .analyzer import analyze_css
from .fetcher import fetch_url
from .models import SiteVisualDNA
from .output import create_site_visual_dna, format_report, save_json

__version__ = "0.1.0"
__all__ = [
    "analyze_css",
    "fetch_url",
    "SiteVisualDNA",
    "create_site_visual_dna",
    "format_report",
    "save_json",
]
