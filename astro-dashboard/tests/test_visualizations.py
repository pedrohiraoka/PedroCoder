"""
Tests for visualization modules.

Run with: python -m pytest tests/test_visualizations.py -v
"""

import pytest
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.visualizations.alert_map import (
    create_alert_sky_map,
    create_alert_type_pie_chart,
    create_magnitude_histogram,
    create_alert_time_series
)
from src.visualizations.linked_views import (
    create_catalog_scatter,
    create_magnitude_redshift_plot,
    create_fwhm_ellipticity_plot,
    calculate_selection_statistics
)


class TestAlertMap:
    """Tests for alert map visualizations."""
    
    def test_create_alert_sky_map(self):
        """Test sky map creation."""
        events = [
            {"ra": 45.0, "dec": 30.0, "type": "GRB", "magnitude": 12.5, 
             "priority": 1, "id": "TEST-001", "timestamp": "2024-01-01T00:00:00"},
            {"ra": 90.0, "dec": -15.0, "type": "SN", "magnitude": 16.0,
             "priority": 2, "id": "TEST-002", "timestamp": "2024-01-01T01:00:00"}
        ]
        
        fig = create_alert_sky_map(events)
        
        assert fig is not None
        assert len(fig.data) > 0
    
    def test_create_alert_sky_map_empty(self):
        """Test sky map with no events."""
        fig = create_alert_sky_map([])
        
        assert fig is not None
        # Should have placeholder annotation
        assert len(fig.layout.annotations) > 0
    
    def test_create_alert_type_pie_chart(self):
        """Test pie chart creation."""
        events = [
            {"type": "GRB"}, {"type": "GRB"}, {"type": "SN"},
            {"type": "SN"}, {"type": "SN"}, {"type": "Asteroid"}
        ]
        
        fig = create_alert_type_pie_chart(events)
        
        assert fig is not None
        assert len(fig.data) > 0
    
    def test_create_magnitude_histogram(self):
        """Test histogram creation."""
        events = [{"magnitude": m} for m in [12, 14, 15, 16, 18, 20, 22]]
        
        fig = create_magnitude_histogram(events)
        
        assert fig is not None
        assert len(fig.data) > 0
    
    def test_create_alert_time_series(self):
        """Test time series creation."""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        events = [
            {"timestamp": (now - timedelta(hours=h)).isoformat()}
            for h in range(10)
        ]
        
        fig = create_alert_time_series(events, hours=24)
        
        assert fig is not None
        assert len(fig.data) > 0


class TestLinkedViews:
    """Tests for linked view visualizations."""
    
    @pytest.fixture
    def sample_catalog(self):
        """Create sample catalog DataFrame."""
        n = 1000
        return pd.DataFrame({
            "id": np.arange(n),
            "ra": np.random.uniform(0, 360, n),
            "dec": np.random.uniform(-90, 90, n),
            "magnitude": np.random.normal(18, 2, n),
            "redshift": np.random.exponential(0.3, n),
            "fwhm": np.random.normal(1.5, 0.5, n),
            "ellipticity": np.random.beta(2, 5, n),
            "snr": np.random.normal(20, 10, n),
            "class": np.random.choice(["STAR", "GALAXY", "QSO"], n)
        })
    
    def test_create_catalog_scatter(self, sample_catalog):
        """Test catalog scatter plot."""
        fig = create_catalog_scatter(sample_catalog)
        
        assert fig is not None
        assert len(fig.data) > 0
    
    def test_create_catalog_scatter_with_selection(self, sample_catalog):
        """Test scatter plot with selected points."""
        selected_ids = {0, 1, 2, 10, 50}
        
        fig = create_catalog_scatter(sample_catalog, selected_ids=selected_ids)
        
        assert fig is not None
        # Should have two traces: selected and unselected
        assert len(fig.data) == 2
    
    def test_create_magnitude_redshift_plot(self, sample_catalog):
        """Test magnitude-redshift plot."""
        fig = create_magnitude_redshift_plot(sample_catalog)
        
        assert fig is not None
        assert len(fig.data) > 0
    
    def test_create_fwhm_ellipticity_plot(self, sample_catalog):
        """Test FWHM-ellipticity plot."""
        fig = create_fwhm_ellipticity_plot(sample_catalog)
        
        assert fig is not None
        assert len(fig.data) > 0
    
    def test_calculate_selection_statistics(self, sample_catalog):
        """Test selection statistics calculation."""
        selected_ids = {0, 1, 2, 3, 4}
        
        stats = calculate_selection_statistics(sample_catalog, selected_ids)
        
        assert stats["count"] == 5
        assert "ra_range" in stats
        assert "dec_range" in stats
        assert "magnitude_avg" in stats
    
    def test_calculate_selection_statistics_empty(self, sample_catalog):
        """Test statistics with no selection."""
        stats = calculate_selection_statistics(sample_catalog, set())
        
        assert stats["count"] == 0


class TestVisualizationDataValidation:
    """Tests for data validation in visualizations."""
    
    def test_invalid_coordinates_handling(self):
        """Test handling of invalid coordinates."""
        events = [
            {"ra": float('nan'), "dec": 30.0, "type": "GRB", 
             "magnitude": 12.5, "priority": 1, "id": "BAD-001"}
        ]
        
        # Should not crash
        fig = create_alert_sky_map(events)
        assert fig is not None
    
    def test_missing_columns_handling(self):
        """Test handling of missing columns."""
        df = pd.DataFrame({"ra": [1, 2, 3], "dec": [1, 2, 3]})
        
        # Should handle missing magnitude/redshift gracefully
        fig = create_magnitude_redshift_plot(df)
        assert fig is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
