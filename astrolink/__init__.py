"""
AstroLink - Your Intelligent Astronomical Laboratory

A modular desktop application for astronomical workflows including
observation planning, data reduction, analysis, modeling, and publishing.
"""

__version__ = "1.0.0"
__author__ = "AstroLink Team"
__license__ = "MIT"

from .core.app import Application
from .core.project import Project

__all__ = ["Application", "Project"]
