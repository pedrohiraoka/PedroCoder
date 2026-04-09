"""Unit tests for OrbitGuard core modules."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """Tests for configuration module."""

    def test_config_initialization(self):
        """Test that config initializes with default values."""
        from utils.config import config
        
        assert config.CACHE_EXPIRY_HOURS == 24
        assert config.BATCH_CHUNK_SIZE == 50
        assert config.DEFAULT_SEARCH_RADIUS_ARCSEC == 5.0
        assert config.JPL_HORIZONS_RATE_LIMIT == 10

    def test_cache_path_creation(self):
        """Test that cache path property creates directory."""
        from utils.config import config
        
        cache_path = config.cache_db_path
        assert cache_path.parent.exists() or cache_path.parent == Path('./orbitguard_cache')


class TestCacheManager:
    """Tests for cache management."""

    def test_cache_set_and_get(self, tmp_path):
        """Test basic cache set and get operations."""
        from utils.cache import CacheManager
        
        db_path = tmp_path / "test_cache.db"
        cache = CacheManager(db_path=db_path)
        
        # Set a value
        cache.set("test_endpoint", {"key": "value"}, {"data": "test"})
        
        # Get the value back
        result = cache.get("test_endpoint", {"key": "value"})
        assert result == {"data": "test"}

    def test_cache_miss(self, tmp_path):
        """Test cache miss returns None."""
        from utils.cache import CacheManager
        
        db_path = tmp_path / "test_cache.db"
        cache = CacheManager(db_path=db_path)
        
        result = cache.get("nonexistent", {"key": "value"})
        assert result is None

    def test_cache_key_generation(self, tmp_path):
        """Test that cache keys are consistent."""
        from utils.cache import CacheManager
        
        db_path = tmp_path / "test_cache.db"
        cache = CacheManager(db_path=db_path)
        
        key1 = cache._generate_key("endpoint", {"a": 1, "b": 2})
        key2 = cache._generate_key("endpoint", {"b": 2, "a": 1})  # Different order
        
        # Keys should be the same despite parameter order
        assert key1 == key2

    def test_cache_stats(self, tmp_path):
        """Test cache statistics."""
        from utils.cache import CacheManager
        
        db_path = tmp_path / "test_cache.db"
        cache = CacheManager(db_path=db_path)
        
        cache.set("ep1", {"k": "v1"}, "data1")
        cache.set("ep1", {"k": "v2"}, "data2")
        cache.set("ep2", {"k": "v3"}, "data3")
        
        stats = cache.get_stats()
        assert stats["total_entries"] == 3
        assert "ep1" in stats["by_endpoint"]
        assert stats["by_endpoint"]["ep1"] == 2


class TestCatalogAPI:
    """Tests for catalog API wrapper."""

    @patch('core.catalog.EXOPLANET_AVAILABLE', False)
    def test_api_handles_missing_exoplanet_archive(self):
        """Test graceful handling when exoplanet archive is unavailable."""
        from core.catalog import CatalogAPI
        
        api = CatalogAPI(use_cache=False)
        result = api.get_exoplanet_by_hostname("HD 209458")
        assert result is None

    def test_exoplanet_data_structure(self):
        """Test ExoplanetData dataclass structure."""
        from core.catalog import ExoplanetData
        
        data = ExoplanetData(
            planet_name="Test Planet",
            hostname="HD 123456",
            ra=180.0,
            dec=-30.0,
            period_days=3.5,
            transit_depth_ppm=1000.0,
            planet_radius_earth=1.5,
            stellar_mag=8.5,
            discovery_year=2020
        )
        
        assert data.planet_name == "Test Planet"
        assert data.period_days == 3.5
        assert data.ra == 180.0


class TestTransitValidator:
    """Tests for transit validation module."""

    def test_validation_result_structure(self):
        """Test ValidationResult dataclass structure."""
        from core.validator import ValidationResult, ValidationStatus
        from datetime import datetime, timezone
        
        result = ValidationResult(
            status=ValidationStatus.GREEN,
            target_hostname="HD 209458",
            target_ra=345.0,
            target_dec=-50.0,
            obs_time_utc=datetime.now(timezone.utc),
            exoplanet_data=None
        )
        
        assert result.status == ValidationStatus.GREEN
        assert result.contaminants == []
        assert result.lightcurve_available is False

    def test_validation_status_enum(self):
        """Test validation status enum values."""
        from core.validator import ValidationStatus
        
        assert ValidationStatus.GREEN.value == "GREEN"
        assert ValidationStatus.YELLOW.value == "YELLOW"
        assert ValidationStatus.RED.value == "RED"

    def test_validate_transit_function_error_handling(self):
        """Test validate_transit handles invalid coordinates."""
        from core.validator import validate_transit
        from datetime import datetime, timezone
        
        # Invalid coordinate format
        result = validate_transit("invalid", datetime.now(timezone.utc), use_coords=True)
        assert "error" in result
        
        # Valid format but wrong number of components
        result = validate_transit("180.0", datetime.now(timezone.utc), use_coords=True)
        assert "error" in result

    @patch('core.validator.TransitValidator._check_asteroid_contamination')
    def test_validator_with_mock_asteroid_check(self, mock_asteroid):
        """Test validator with mocked asteroid checking."""
        from core.validator import TransitValidator, ValidationStatus, ContaminantInfo
        from core.catalog import ExoplanetData
        from datetime import datetime, timezone
        
        # Mock asteroid check to return a contaminant
        mock_asteroid.return_value = [
            ContaminantInfo(
                object_id="1 Ceres",
                object_type="asteroid",
                ra=180.0,
                dec=-30.0,
                separation_arcsec=2.5,
                magnitude=7.0
            )
        ]
        
        validator = TransitValidator()
        
        # Create mock exoplanet data
        exoplanet_data = ExoplanetData(
            planet_name="Test b",
            hostname="HD 123456",
            ra=180.0,
            dec=-30.0,
            period_days=3.5,
            transit_depth_ppm=1000.0,
            planet_radius_earth=1.5,
            stellar_mag=8.5,
            discovery_year=2020
        )
        
        result = validator.validate_by_coords(
            ra=180.0,
            dec=-30.0,
            obs_time=datetime.now(timezone.utc),
            exoplanet_data=exoplanet_data,
            check_asteroids=True
        )
        
        assert len(result.contaminants) == 1
        assert result.contaminants[0].object_id == "1 Ceres"
        assert result.status == ValidationStatus.YELLOW  # Within warning threshold

    def test_status_determination_critical_contamination(self):
        """Test status determination with critical contamination."""
        from core.validator import TransitValidator, ValidationStatus, ContaminantInfo
        from core.catalog import ExoplanetData
        from utils.config import config
        
        validator = TransitValidator()
        
        # Create contaminant within critical threshold
        contaminant = ContaminantInfo(
            object_id="Test Asteroid",
            object_type="asteroid",
            ra=180.0,
            dec=-30.0,
            separation_arcsec=config.MIN_SEPARATION_CRITICAL_ARCSEC - 0.5,
            magnitude=10.0
        )
        
        exoplanet_data = ExoplanetData(
            planet_name="Test b",
            hostname="HD 123456",
            ra=180.0,
            dec=-30.0,
            period_days=3.5,
            transit_depth_ppm=1000.0,
            planet_radius_earth=1.5,
            stellar_mag=8.5,
            discovery_year=2020
        )
        
        status = validator._determine_status([contaminant], exoplanet_data)
        assert status == ValidationStatus.RED

    def test_tic_id_extraction(self):
        """Test TIC ID extraction from hostnames."""
        from core.validator import TransitValidator
        
        validator = TransitValidator()
        
        assert validator._extract_tic_id("TIC 123456789") == "TIC 123456789"
        assert validator._extract_tic_id("tic 987654321") == "TIC 987654321"
        assert validator._extract_tic_id("HD 209458") is None
        assert validator._extract_tic_id("Kepler-10") is None


class TestAngularSeparation:
    """Tests for angular separation calculations."""

    def test_skycoord_separation(self):
        """Test astropy SkyCoord separation calculation."""
        from astropy.coordinates import SkyCoord
        from astropy import units as u
        
        coord1 = SkyCoord(ra=0*u.deg, dec=0*u.deg)
        coord2 = SkyCoord(ra=0.001*u.deg, dec=0*u.deg)
        
        separation = coord1.separation(coord2).arcsec
        assert abs(separation - 3.6) < 0.1  # ~3.6 arcseconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
