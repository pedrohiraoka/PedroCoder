"""
Alert Parser - Filters, prioritizes and parses astronomical alerts.

Processes VOEvent data for display and action in the dashboard.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

import pandas as pd
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertParser:
    """Parses and processes astronomical alert data."""
    
    def __init__(self):
        """Initialize alert parser."""
        self.processed_alerts: List[Dict[str, Any]] = []
        
    def parse_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse raw event data into standardized format.
        
        Args:
            events: List of raw event dictionaries.
            
        Returns:
            List of parsed event dictionaries.
        """
        parsed = []
        
        for event in events:
            try:
                parsed_event = self._parse_single_event(event)
                parsed.append(parsed_event)
            except Exception as e:
                logger.warning(f"Error parsing event {event.get('id', 'unknown')}: {e}")
                continue
        
        self.processed_alerts = parsed
        logger.info(f"Parsed {len(parsed)} alerts")
        return parsed
    
    def _parse_single_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single event.
        
        Args:
            event: Raw event dictionary.
            
        Returns:
            Parsed event dictionary.
        """
        # Extract and standardize fields
        parsed = {
            "id": event.get("id", "UNKNOWN"),
            "type": event.get("type", "Unknown"),
            "ra": float(event.get("ra", 0)),
            "dec": float(event.get("dec", 0)),
            "magnitude": float(event.get("magnitude", 99)),
            "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
            "priority": int(event.get("priority", 5)),
            "source": event.get("source", "Unknown"),
        }
        
        # Calculate additional metadata
        parsed["age_hours"] = self._calculate_age_hours(parsed["timestamp"])
        parsed["visibility"] = self._calculate_visibility(parsed["ra"], parsed["dec"])
        parsed["urgency_score"] = self._calculate_urgency(
            parsed["type"], 
            parsed["magnitude"],
            parsed["age_hours"]
        )
        
        return parsed
    
    def _calculate_age_hours(self, timestamp: str) -> float:
        """
        Calculate age of event in hours.
        
        Args:
            timestamp: ISO format timestamp.
            
        Returns:
            Age in hours.
        """
        try:
            event_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.utcnow()
            
            # Handle timezone-naive datetimes
            if event_time.tzinfo is None:
                age = now - event_time
            else:
                age = now - event_time.replace(tzinfo=None)
            
            return max(0, age.total_seconds() / 3600)
            
        except Exception:
            return 999
    
    def _calculate_visibility(self, ra: float, dec: float) -> str:
        """
        Estimate visibility from observatory location.
        
        Args:
            ra: Right ascension in degrees.
            dec: Declination in degrees.
            
        Returns:
            Visibility status string.
        """
        # Simplified visibility calculation
        # In reality, would need observatory coordinates and current time
        
        # Objects near celestial equator are visible from most locations
        if abs(dec) < 30:
            return "excellent"
        elif abs(dec) < 60:
            return "good"
        elif abs(dec) < 80:
            return "limited"
        else:
            return "poor"
    
    def _calculate_urgency(self, event_type: str, magnitude: float, 
                          age_hours: float) -> float:
        """
        Calculate urgency score for follow-up.
        
        Args:
            event_type: Type of event.
            magnitude: Apparent magnitude.
            age_hours: Age in hours.
            
        Returns:
            Urgency score (higher = more urgent).
        """
        # Base urgency by type
        type_urgency = {
            "GRB": 100,
            "SN": 70,
            "Asteroid": 50,
            "Unknown": 40,
            "Normal": 10
        }
        
        base = type_urgency.get(event_type, 10)
        
        # Brighter objects are more urgent
        mag_factor = max(0, (20 - magnitude) / 10)
        
        # Newer events are more urgent
        age_factor = max(0, 1 - age_hours / 24)
        
        urgency = base * (0.5 + 0.3 * mag_factor + 0.2 * age_factor)
        return round(urgency, 1)
    
    def filter_by_type(self, events: List[Dict], 
                      event_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Filter events by type.
        
        Args:
            events: List of events.
            event_types: List of types to include (None = all).
            
        Returns:
            Filtered list.
        """
        if not event_types:
            return events
        
        return [e for e in events if e["type"] in event_types]
    
    def filter_by_priority(self, events: List[Dict], 
                          max_priority: int) -> List[Dict]:
        """
        Filter events by maximum priority.
        
        Args:
            events: List of events.
            max_priority: Maximum priority value (1-5).
            
        Returns:
            Filtered list.
        """
        return [e for e in events if e["priority"] <= max_priority]
    
    def filter_by_age(self, events: List[Dict], 
                     max_age_hours: float) -> List[Dict]:
        """
        Filter events by maximum age.
        
        Args:
            events: List of events.
            max_age_hours: Maximum age in hours.
            
        Returns:
            Filtered list.
        """
        return [e for e in events if e["age_hours"] <= max_age_hours]
    
    def filter_by_magnitude(self, events: List[Dict], 
                           min_mag: float, max_mag: float) -> List[Dict]:
        """
        Filter events by magnitude range.
        
        Args:
            events: List of events.
            min_mag: Minimum magnitude (brightest).
            max_mag: Maximum magnitude (faintest).
            
        Returns:
            Filtered list.
        """
        return [e for e in events if min_mag <= e["magnitude"] <= max_mag]
    
    def sort_by_urgency(self, events: List[Dict], 
                       ascending: bool = False) -> List[Dict]:
        """
        Sort events by urgency score.
        
        Args:
            events: List of events.
            ascending: If True, sort lowest urgency first.
            
        Returns:
            Sorted list.
        """
        return sorted(events, key=lambda x: x["urgency_score"], reverse=not ascending)
    
    def group_by_type(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group events by type.
        
        Args:
            events: List of events.
            
        Returns:
            Dictionary mapping types to event lists.
        """
        groups = {}
        for event in events:
            t = event["type"]
            if t not in groups:
                groups[t] = []
            groups[t].append(event)
        return groups
    
    def get_summary_statistics(self, events: List[Dict]) -> Dict[str, Any]:
        """
        Calculate summary statistics for events.
        
        Args:
            events: List of events.
            
        Returns:
            Dictionary with statistics.
        """
        if not events:
            return {"count": 0}
        
        magnitudes = [e["magnitude"] for e in events]
        ages = [e["age_hours"] for e in events]
        urgencies = [e["urgency_score"] for e in events]
        
        type_counts = {}
        for e in events:
            t = e["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "count": len(events),
            "by_type": type_counts,
            "avg_magnitude": round(np.mean(magnitudes), 2),
            "avg_age_hours": round(np.mean(ages), 1),
            "avg_urgency": round(np.mean(urgencies), 1),
            "newest_event_hours": round(min(ages), 1) if ages else None,
            "brightest_magnitude": round(min(magnitudes), 2) if magnitudes else None
        }
    
    def to_dataframe(self, events: List[Dict]) -> pd.DataFrame:
        """
        Convert events to pandas DataFrame.
        
        Args:
            events: List of events.
            
        Returns:
            DataFrame with event data.
        """
        return pd.DataFrame(events)
    
    def detect_anomalies(self, events: List[Dict], 
                        window_hours: float = 1) -> List[Dict]:
        """
        Detect anomalous alert rates.
        
        Args:
            events: List of events.
            window_hours: Time window for rate calculation.
            
        Returns:
            List of anomaly notifications.
        """
        anomalies = []
        
        # Group by type and check rates
        by_type = self.group_by_type(events)
        
        for event_type, type_events in by_type.items():
            recent = [e for e in type_events if e["age_hours"] <= window_hours]
            
            # Flag if unusually high rate
            if len(recent) > 10:  # Threshold
                anomalies.append({
                    "type": "high_rate",
                    "event_type": event_type,
                    "count": len(recent),
                    "window_hours": window_hours,
                    "message": f"High rate of {event_type} alerts: {len(recent)} in {window_hours}h"
                })
        
        return anomalies
