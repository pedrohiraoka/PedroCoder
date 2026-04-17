"""
Tests for data fetchers module.

Run with: python -m pytest tests/test_fetchers.py -v
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_fetchers.voevent_fetcher import VOEventFetcher
from src.data_fetchers.weather_fetcher import WeatherFetcher
from src.data_fetchers.instrument_status import InstrumentStatus
from src.data_fetchers.fits_loader import FITSCatalogLoader


class TestVOEventFetcher:
    """Tests for VOEvent fetcher."""
    
    def test_init(self):
        """Test fetcher initialization."""
        fetcher = VOEventFetcher(use_mock=True)
        assert fetcher.use_mock is True
        assert fetcher.event_cache == []
    
    def test_fetch_events(self):
        """Test event fetching."""
        fetcher = VOEventFetcher(use_mock=True)
        events = fetcher.fetch_events(max_events=10)
        
        assert len(events) == 10
        assert all("id" in e for e in events)
        assert all("type" in e for e in events)
        assert all("ra" in e for e in events)
        assert all("dec" in e for e in events)
        assert all("magnitude" in e for e in events)
    
    def test_filter_by_type(self):
        """Test event type filtering."""
        fetcher = VOEventFetcher(use_mock=True)
        events = fetcher.fetch_events(max_events=50)
        
        # Filter for GRBs only
        grb_events = fetcher.filter_by_type(events, "GRB")
        assert all(e["type"] == "GRB" for e in grb_events)
        
        # All events
        all_events = fetcher.filter_by_type(events, "ALL")
        assert len(all_events) == len(events)
    
    def test_get_statistics(self):
        """Test statistics calculation."""
        fetcher = VOEventFetcher(use_mock=True)
        events = fetcher.fetch_events(max_events=20)
        
        stats = fetcher.get_statistics(events)
        
        assert stats["count"] == 20
        assert "by_type" in stats
        assert "avg_magnitude" in stats
    
    def test_priority_calculation(self):
        """Test priority assignment."""
        fetcher = VOEventFetcher(use_mock=True)
        events = fetcher.fetch_events(max_events=50)
        
        # Check priorities are in valid range
        for event in events:
            assert 1 <= event["priority"] <= 5


class TestWeatherFetcher:
    """Tests for weather fetcher."""
    
    def test_init(self):
        """Test fetcher initialization."""
        fetcher = WeatherFetcher(use_mock=True)
        assert fetcher.use_mock is True
    
    def test_fetch_conditions(self):
        """Test condition fetching."""
        fetcher = WeatherFetcher(use_mock=True)
        conditions = fetcher.fetch_conditions()
        
        assert "seeing" in conditions
        assert "humidity" in conditions
        assert "wind_speed" in conditions
        assert "temperature" in conditions
        assert "cloud_cover" in conditions
        
        # Check value ranges
        assert 0.5 <= conditions["seeing"] <= 5.0
        assert 20 <= conditions["humidity"] <= 95
        assert 0 <= conditions["wind_speed"] <= 60
    
    def test_status_determination(self):
        """Test status classification."""
        fetcher = WeatherFetcher(use_mock=True)
        conditions = fetcher.fetch_conditions()
        
        assert conditions["seeing_status"] in ["good", "warning", "bad"]
        assert conditions["humidity_status"] in ["ok", "warning", "alert"]
        assert conditions["wind_status"] in ["ok", "warning", "alert"]
    
    def test_is_observing_possible(self):
        """Test observing possibility check."""
        fetcher = WeatherFetcher(use_mock=True)
        
        # Should generally be possible with mock data
        result = fetcher.is_observing_possible()
        assert isinstance(result, bool)


class TestInstrumentStatus:
    """Tests for instrument status fetcher."""
    
    def test_init(self):
        """Test fetcher initialization."""
        fetcher = InstrumentStatus(use_mock=True)
        assert fetcher.use_mock is True
    
    def test_fetch_all_status(self):
        """Test status fetching."""
        fetcher = InstrumentStatus(use_mock=True)
        instruments = fetcher.fetch_all_status()
        
        assert "main_camera" in instruments
        assert "guide_camera" in instruments
        assert "mount" in instruments
        
        # Check camera status
        camera = instruments["main_camera"]
        assert "ccd_temperature" in camera
        assert "shutter" in camera
        assert "health" in camera
    
    def test_health_indicators(self):
        """Test health status values."""
        fetcher = InstrumentStatus(use_mock=True)
        instruments = fetcher.fetch_all_status()
        
        for name, status in instruments.items():
            assert status["health"] in ["good", "warning", "critical"]
    
    def test_get_critical_alerts(self):
        """Test alert generation."""
        fetcher = InstrumentStatus(use_mock=True)
        fetcher.fetch_all_status()
        
        alerts = fetcher.get_critical_alerts()
        assert isinstance(alerts, list)
        
        for alert in alerts:
            assert "instrument" in alert
            assert "severity" in alert
            assert "message" in alert


class TestFITSCatalogLoader:
    """Tests for FITS catalog loader."""
    
    def test_init(self):
        """Test loader initialization."""
        loader = FITSCatalogLoader(use_mock=True)
        assert loader.use_mock is True
    
    def test_open(self):
        """Test file opening."""
        loader = FITSCatalogLoader(use_mock=True)
        result = loader.open()
        assert result is True
    
    def test_get_catalog_info(self):
        """Test catalog info retrieval."""
        loader = FITSCatalogLoader(use_mock=True)
        info = loader.get_catalog_info()
        
        assert "n_objects" in info
        assert "columns" in info
        assert "filename" in info
    
    def test_read_chunk(self):
        """Test chunked reading."""
        loader = FITSCatalogLoader(use_mock=True)
        loader.open()
        
        df = loader.read_chunk(0, 100)
        
        assert len(df) == 100
        assert "ra" in df.columns
        assert "dec" in df.columns
        assert "magnitude" in df.columns
    
    def test_read_all(self):
        """Test full catalog reading."""
        loader = FITSCatalogLoader(use_mock=True)
        
        df = loader.read_all(max_rows=1000)
        
        assert len(df) == 1000
        assert len(df.columns) > 0
    
    def test_statistics(self):
        """Test statistics calculation."""
        loader = FITSCatalogLoader(use_mock=True)
        
        stats = loader.get_statistics()
        
        assert "n_objects" in stats
        assert "magnitude" in stats
        assert "fwhm" in stats
        
        # Check magnitude stats
        mag_stats = stats["magnitude"]
        assert "mean" in mag_stats
        assert "std" in mag_stats
        assert "min" in mag_stats
        assert "max" in mag_stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
