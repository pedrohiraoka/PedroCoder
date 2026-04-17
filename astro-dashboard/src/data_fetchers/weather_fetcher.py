"""
Weather Fetcher - Retrieves observatory environmental conditions.

Provides seeing, humidity, wind, temperature, and cloud cover data.
Uses mock data by default for offline operation.
"""

import random
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from src.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherFetcher:
    """Fetches weather and environmental conditions for the observatory."""
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize weather fetcher.
        
        Args:
            use_mock: If True, use simulated data instead of real sensors/APIs.
        """
        self.use_mock = use_mock
        self.last_update: Optional[datetime] = None
        self.current_conditions: Dict[str, Any] = {}
        
    def fetch_conditions(self) -> Dict[str, Any]:
        """
        Fetch current weather conditions.
        
        Returns:
            Dictionary with environmental measurements.
        """
        try:
            if self.use_mock:
                conditions = self._fetch_mock_conditions()
            else:
                conditions = self._fetch_real_conditions()
            
            self.current_conditions = conditions
            self.last_update = datetime.utcnow()
            logger.debug(f"Fetched weather conditions: {conditions}")
            return conditions
            
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return self._fetch_mock_conditions()
    
    def _fetch_mock_conditions(self) -> Dict[str, Any]:
        """
        Generate simulated weather conditions.
        
        Returns:
            Dictionary with mock environmental data.
        """
        # Simulate realistic variations
        seeing = random.gauss(2.0, 0.5)  # arcseconds
        seeing = max(0.5, min(5.0, seeing))  # Clamp to reasonable range
        
        humidity = random.gauss(60, 15)  # percent
        humidity = max(20, min(95, humidity))
        
        wind_speed = random.gauss(15, 8)  # km/h
        wind_speed = max(0, min(60, wind_speed))
        
        temperature = random.gauss(15, 5)  # Celsius (ambient)
        
        cloud_cover = random.uniform(0, 100)  # percent
        
        # Determine status based on thresholds
        seeing_status = "good" if seeing < 1.5 else ("warning" if seeing < 3.0 else "bad")
        humidity_status = "alert" if humidity > 85 else ("warning" if humidity > 75 else "ok")
        wind_status = "alert" if wind_speed > 40 else ("warning" if wind_speed > 30 else "ok")
        
        conditions = {
            "seeing": round(seeing, 2),
            "seeing_status": seeing_status,
            "humidity": round(humidity, 1),
            "humidity_status": humidity_status,
            "wind_speed": round(wind_speed, 1),
            "wind_status": wind_status,
            "temperature": round(temperature, 1),
            "cloud_cover": round(cloud_cover, 1),
            "timestamp": datetime.utcnow().isoformat(),
            "observatory": "Observatório Nacional"
        }
        
        return conditions
    
    def _fetch_real_conditions(self) -> Dict[str, Any]:
        """
        Fetch real weather data from sensors or API.
        
        Returns:
            Dictionary with real environmental data.
        """
        # Placeholder for real implementation
        # Could integrate with:
        # - Local weather station API
        # - AllSky camera data
        # - DIMM (Differential Image Motion Monitor) readings
        logger.warning("Real weather fetching not implemented, using mock")
        return self._fetch_mock_conditions()
    
    def get_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get historical weather data (mock).
        
        Args:
            hours: Number of hours of history to generate.
            
        Returns:
            List of historical condition dictionaries.
        """
        history = []
        base_time = datetime.utcnow()
        
        for h in range(hours):
            # Create time point
            time_point = base_time - timedelta(hours=h)
            
            # Generate correlated data (seeing tends to improve at night)
            hour_of_day = time_point.hour
            night_factor = 0.8 if 20 <= hour_of_day <= 6 else 1.2
            
            seeing = random.gauss(2.0 * night_factor, 0.5)
            seeing = max(0.5, min(5.0, seeing))
            
            humidity = random.gauss(60, 15)
            humidity = max(20, min(95, humidity))
            
            history.append({
                "timestamp": time_point.isoformat(),
                "seeing": round(seeing, 2),
                "humidity": round(humidity, 1),
                "temperature": round(random.gauss(15, 5), 1),
                "wind_speed": round(random.gauss(15, 8), 1)
            })
        
        return history
    
    def is_observing_possible(self) -> bool:
        """
        Check if current conditions allow observations.
        
        Returns:
            True if conditions are acceptable for observing.
        """
        if not self.current_conditions:
            return True
        
        # Block observing if any critical condition
        if self.current_conditions.get("humidity_status") == "alert":
            return False
        if self.current_conditions.get("wind_status") == "alert":
            return False
        if self.current_conditions.get("cloud_cover", 0) > 90:
            return False
        
        return True
    
    def get_summary(self) -> str:
        """
        Get human-readable summary of conditions.
        
        Returns:
            Formatted string summary.
        """
        if not self.current_conditions:
            return "No data available"
        
        c = self.current_conditions
        return (
            f"Seeing: {c['seeing']}\" ({c['seeing_status']}) | "
            f"Humidity: {c['humidity']}% | "
            f"Wind: {c['wind_speed']} km/h | "
            f"Temp: {c['temperature']}°C | "
            f"Cloud: {c['cloud_cover']}%"
        )


# Import timedelta for history function
from datetime import timedelta
