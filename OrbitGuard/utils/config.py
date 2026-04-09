"""
Configuration constants and settings for OrbitGuard.

This module defines API limits, cache paths, and other configuration
parameters used throughout the application.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Config:
    """Application configuration with immutable defaults."""

    # Cache settings
    CACHE_DIR: Path = Path("./orbitguard_cache")
    CACHE_DB_NAME: str = "catalog_cache.db"
    CACHE_EXPIRY_HOURS: int = 24

    # API Rate limits (requests per minute)
    JPL_HORIZONS_RATE_LIMIT: int = 10
    EXOPLANET_ARCHIVE_RATE_LIMIT: int = 10
    GAIA_RATE_LIMIT: int = 5

    # Search parameters
    DEFAULT_SEARCH_RADIUS_ARCSEC: float = 5.0
    DEFAULT_FOV_DEG: float = 1.0
    BATCH_CHUNK_SIZE: int = 50
    MAX_WORKERS: int = 4

    # Ephemeris settings
    EPHEMERIS_STEP_MINUTES: int = 5
    DEFAULT_EPH_START_HOURS: int = -6
    DEFAULT_EPH_END_HOURS: int = 6

    # Validation thresholds
    MIN_SEPARATION_WARNING_ARCSEC: float = 3.0
    MIN_SEPARATION_CRITICAL_ARCSEC: float = 1.5

    @property
    def cache_db_path(self) -> Path:
        """Return full path to cache database."""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return self.CACHE_DIR / self.CACHE_DB_NAME


# Global config instance
config = Config()
