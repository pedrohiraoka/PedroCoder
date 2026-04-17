"""
VOEvent Fetcher - Polls VOEvent brokers and TNS for astronomical transients.

Uses astroquery for VOEvent access and provides fallback mock data when offline.
"""

import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy as np

try:
    from astroquery.voevent import voevent
    ASTROQUERY_AVAILABLE = True
except ImportError:
    ASTROQUERY_AVAILABLE = False

from src.utils.logger import get_logger
from src.utils.time_utils import mjd_to_datetime

logger = get_logger(__name__)


class VOEventFetcher:
    """Fetches and parses VOEvent alerts from brokers."""
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize VOEvent fetcher.
        
        Args:
            use_mock: If True, use simulated data instead of real API calls.
        """
        self.use_mock = use_mock
        self.last_fetch_time: Optional[datetime] = None
        self.event_cache: List[Dict[str, Any]] = []
        
    def fetch_events(self, max_events: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch recent VOEvent alerts.
        
        Args:
            max_events: Maximum number of events to return.
            
        Returns:
            List of event dictionaries with parsed metadata.
        """
        try:
            if self.use_mock or not ASTROQUERY_AVAILABLE:
                events = self._fetch_mock_events(max_events)
            else:
                events = self._fetch_real_events(max_events)
            
            self.last_fetch_time = datetime.utcnow()
            self.event_cache = events
            logger.info(f"Fetched {len(events)} VOEvent alerts")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching VOEvents: {e}")
            # Fallback to mock data on error
            return self._fetch_mock_events(max_events)
    
    def _fetch_real_events(self, max_events: int) -> List[Dict[str, Any]]:
        """
        Fetch real events from VOEvent broker (when online).
        
        Args:
            max_events: Maximum number of events.
            
        Returns:
            List of parsed events.
        """
        events = []
        # Note: Real VOEvent querying requires proper setup and network access
        # This is a placeholder for actual implementation
        logger.warning("Real VOEvent fetching not fully implemented, using mock")
        return self._fetch_mock_events(max_events)
    
    def _fetch_mock_events(self, max_events: int) -> List[Dict[str, Any]]:
        """
        Generate simulated VOEvent alerts for testing/demo.
        
        Args:
            max_events: Maximum number of events to generate.
            
        Returns:
            List of mock event dictionaries.
        """
        event_types = ["GRB", "SN", "Asteroid", "Unknown", "Normal"]
        event_weights = [0.05, 0.15, 0.20, 0.10, 0.50]  # Probability distribution
        
        events = []
        base_time = datetime.utcnow()
        
        for i in range(max_events):
            event_type = random.choices(event_types, weights=event_weights)[0]
            
            # Generate random coordinates (full sky)
            ra = random.uniform(0, 360)
            dec = random.uniform(-90, 90)
            
            # Generate magnitude based on event type
            if event_type == "GRB":
                magnitude = random.uniform(8, 14)
            elif event_type == "SN":
                magnitude = random.uniform(14, 20)
            else:
                magnitude = random.uniform(12, 22)
            
            # Time offset (events within last 24 hours)
            time_offset = timedelta(minutes=random.randint(0, 1440))
            event_time = base_time - time_offset
            
            event = {
                "id": f"VOE-{i:06d}",
                "type": event_type,
                "ra": ra,
                "dec": dec,
                "magnitude": round(magnitude, 2),
                "timestamp": event_time.isoformat(),
                "mjd": (event_time - datetime(1858, 11, 17)).total_seconds() / 86400,
                "priority": self._calculate_priority(event_type, magnitude),
                "source": "Mock Broker",
                "coordinates": f"{ra:.4f}h {dec:+.4f}d"
            }
            events.append(event)
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events
    
    def _calculate_priority(self, event_type: str, magnitude: float) -> int:
        """
        Calculate event priority score (1=highest, 5=lowest).
        
        Args:
            event_type: Type of astronomical event.
            magnitude: Apparent magnitude.
            
        Returns:
            Priority score.
        """
        base_priority = {
            "GRB": 1,
            "SN": 2,
            "Asteroid": 3,
            "Unknown": 3,
            "Normal": 4
        }
        
        priority = base_priority.get(event_type, 4)
        
        # Adjust priority based on brightness (brighter = higher priority)
        if magnitude < 12:
            priority = max(1, priority - 1)
        elif magnitude > 18:
            priority = min(5, priority + 1)
        
        return priority
    
    def filter_by_type(self, events: List[Dict], event_type: str) -> List[Dict]:
        """
        Filter events by type.
        
        Args:
            events: List of events.
            event_type: Type to filter by ("ALL" for no filtering).
            
        Returns:
            Filtered list of events.
        """
        if event_type == "ALL":
            return events
        return [e for e in events if e["type"] == event_type]
    
    def filter_by_priority(self, events: List[Dict], max_priority: int) -> List[Dict]:
        """
        Filter events by maximum priority threshold.
        
        Args:
            events: List of events.
            max_priority: Maximum priority value (1-5).
            
        Returns:
            Filtered list of events.
        """
        return [e for e in events if e["priority"] <= max_priority]
    
    def get_statistics(self, events: List[Dict]) -> Dict[str, Any]:
        """
        Calculate statistics for a set of events.
        
        Args:
            events: List of events.
            
        Returns:
            Dictionary with statistical summaries.
        """
        if not events:
            return {"count": 0}
        
        type_counts = {}
        for event in events:
            t = event["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        
        magnitudes = [e["magnitude"] for e in events]
        
        return {
            "count": len(events),
            "by_type": type_counts,
            "avg_magnitude": round(np.mean(magnitudes), 2),
            "min_magnitude": round(min(magnitudes), 2),
            "max_magnitude": round(max(magnitudes), 2),
            "last_update": self.last_fetch_time.isoformat() if self.last_fetch_time else None
        }
