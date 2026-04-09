"""
OrbitGuard Core Module.

Módulos principais para validação de trânsitos, cálculo de efemérides
e cruzamento de dados astronômicos.
"""

from .catalog import ExoplanetCatalog, LightCurveSearch, JPLHorizonsQuery
from .validator import TransitValidator, ValidationResult
from .ephemeris import EphemerisCalculator, OccultationPrioritizer
from .cross_match import BatchCrossMatcher, CrossMatchResult

__all__ = [
    "ExoplanetCatalog",
    "LightCurveSearch",
    "JPLHorizonsQuery",
    "TransitValidator",
    "ValidationResult",
    "EphemerisCalculator",
    "OccultationPrioritizer",
    "BatchCrossMatcher",
    "CrossMatchResult",
]
