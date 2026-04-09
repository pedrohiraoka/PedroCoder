"""
OrbitGuard Core Module.

Módulos principais para validação de trânsitos, cálculo de efemérides
e cruzamento de dados astronômicos.
"""

from .catalog import CatalogAPI, ExoplanetData, AsteroidData, StarCandidate
from .validator import TransitValidator, ValidationResult
from .ephemeris import EphemerisCalculator, OccultationPrioritizer, EphemerisData
from .cross_match import BatchCrossMatcher, CrossMatchResult

__all__ = [
    "CatalogAPI",
    "ExoplanetData",
    "AsteroidData",
    "StarCandidate",
    "TransitValidator",
    "ValidationResult",
    "EphemerisCalculator",
    "OccultationPrioritizer",
    "EphemerisData",
    "BatchCrossMatcher",
    "CrossMatchResult",
]
