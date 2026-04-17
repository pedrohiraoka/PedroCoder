"""
Instrument Status - Monitors telescope and detector health.

Tracks CCD temperatures, shutter status, filter wheels, guiding, and spectrographs.
"""

import random
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from src.utils.logger import get_logger

logger = get_logger(__name__)


class InstrumentStatus:
    """Monitors status of telescope instruments and detectors."""
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize instrument status monitor.
        
        Args:
            use_mock: If True, use simulated data instead of real instrument control system.
        """
        self.use_mock = use_mock
        self.last_update: Optional[datetime] = None
        self.instruments: Dict[str, Dict[str, Any]] = {}
        
    def fetch_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch status of all instruments.
        
        Returns:
            Dictionary mapping instrument names to their status dictionaries.
        """
        try:
            if self.use_mock:
                status = self._fetch_mock_status()
            else:
                status = self._fetch_real_status()
            
            self.instruments = status
            self.last_update = datetime.utcnow()
            logger.debug(f"Fetched instrument status for {len(status)} instruments")
            return status
            
        except Exception as e:
            logger.error(f"Error fetching instrument status: {e}")
            return self._fetch_mock_status()
    
    def _fetch_mock_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate simulated instrument status.
        
        Returns:
            Dictionary with mock instrument data.
        """
        instruments = {}
        
        # Main camera (CCD)
        ccd_temp = random.gauss(-105, 3)  # Celsius (cooled CCD)
        ccd_temp_status = "ok" if ccd_temp < -100 else ("warning" if ccd_temp < -95 else "critical")
        
        instruments["main_camera"] = {
            "name": "Main Camera",
            "type": "CCD",
            "status": "active",
            "ccd_temperature": round(ccd_temp, 1),
            "ccd_temp_status": ccd_temp_status,
            "shutter": random.choice(["open", "closed"]),
            "filter_wheel": f"Filter_{random.randint(1, 7)}",
            "gain": random.choice([1.0, 1.5, 2.0]),
            "readout_mode": "normal",
            "last_exposure": random.randint(60, 300),  # seconds
            "health": "good" if ccd_temp_status == "ok" else "warning"
        }
        
        # Guide camera
        guide_lock = random.random() > 0.1  # 90% chance of good lock
        instruments["guide_camera"] = {
            "name": "Guide Camera",
            "type": "GUIDER",
            "status": "active",
            "lock_status": "locked" if guide_lock else "searching",
            "rms_error": round(random.uniform(0.1, 0.8), 2) if guide_lock else round(random.uniform(1.0, 3.0), 2),
            "star_brightness": round(random.uniform(1000, 50000), 0),
            "health": "good" if guide_lock else "warning"
        }
        
        # Spectrograph
        spec_temp = random.gauss(20, 1)  # Celsius (temperature stabilized)
        instruments["spectrograph"] = {
            "name": "Optical Spectrograph",
            "type": "SPECTROGRAPH",
            "status": random.choice(["active", "standby"]),
            "temperature": round(spec_temp, 1),
            "grating": random.choice(["R1000", "R2000", "R4000"]),
            "slit_width": random.choice(["1.0\"", "2.0\"", "5.0\""]),
            "coverage": "380-900nm",
            "health": "good"
        }
        
        # Telescope mount
        wind_shake = random.random() > 0.95  # 5% chance of wind shake
        instruments["mount"] = {
            "name": "Telescope Mount",
            "type": "MOUNT",
            "status": "tracking",
            "ra": round(random.uniform(0, 24), 4),
            "dec": round(random.uniform(-90, 90), 4),
            "tracking_rate": round(random.gauss(1.0, 0.01), 3),
            "wind_shake": wind_shake,
            "encoder_status": "ok",
            "health": "warning" if wind_shake else "good"
        }
        
        # Filter wheel mechanism
        instruments["filter_wheel"] = {
            "name": "Filter Wheel",
            "type": "FILTERWHEEL",
            "status": "ready",
            "current_filter": f"Luminance_{random.randint(1, 3)}",
            "position_accuracy": "ok",
            "motor_current": round(random.uniform(0.5, 2.0), 2),
            "health": "good"
        }
        
        return instruments
    
    def _fetch_real_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch real instrument status from control system.
        
        Returns:
            Dictionary with real instrument data.
        """
        # Placeholder for real implementation
        # Could integrate with:
        # - EPICS control system
        # - ASCOM drivers
        # - Custom instrument APIs
        logger.warning("Real instrument status not implemented, using mock")
        return self._fetch_mock_status()
    
    def get_critical_alerts(self) -> List[Dict[str, Any]]:
        """
        Get list of critical instrument alerts.
        
        Returns:
            List of alert dictionaries for instruments with issues.
        """
        alerts = []
        
        for name, status in self.instruments.items():
            health = status.get("health", "unknown")
            
            if health == "critical":
                alerts.append({
                    "instrument": name,
                    "severity": "critical",
                    "message": f"{status['name']} has critical issue",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif health == "warning":
                alerts.append({
                    "instrument": name,
                    "severity": "warning",
                    "message": f"{status['name']} needs attention",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return alerts
    
    def is_ready_for_observation(self) -> bool:
        """
        Check if instruments are ready for observations.
        
        Returns:
            True if all critical systems are healthy.
        """
        if not self.instruments:
            return True
        
        # Check critical instruments
        critical_instruments = ["main_camera", "guide_camera", "mount"]
        
        for inst_name in critical_instruments:
            if inst_name in self.instruments:
                health = self.instruments[inst_name].get("health", "unknown")
                if health == "critical":
                    return False
        
        return True
    
    def get_summary(self) -> str:
        """
        Get human-readable summary of instrument status.
        
        Returns:
            Formatted string summary.
        """
        if not self.instruments:
            return "No instrument data available"
        
        summaries = []
        for name, status in self.instruments.items():
            health_emoji = {"good": "🟢", "warning": "🟡", "critical": "🔴"}.get(
                status.get("health", "unknown"), "⚪"
            )
            summaries.append(f"{health_emoji} {status['name']}")
        
        return " | ".join(summaries)
