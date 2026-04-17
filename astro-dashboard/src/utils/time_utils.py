"""
Time Utilities - Time conversion and formatting for astronomical data.

Handles MJD, UTC, and local time conversions.
"""

from datetime import datetime, timezone
from typing import Optional, Union
import numpy as np


def mjd_to_datetime(mjd: float) -> datetime:
    """
    Convert Modified Julian Date to datetime.
    
    Args:
        mjd: Modified Julian Date.
        
    Returns:
        datetime object in UTC.
    """
    # MJD epoch is 1858-11-17 00:00:00 UTC
    mjd_epoch = datetime(1858, 11, 17, tzinfo=timezone.utc)
    return mjd_epoch + timedelta(days=mjd)


def datetime_to_mjd(dt: datetime) -> float:
    """
    Convert datetime to Modified Julian Date.
    
    Args:
        dt: datetime object.
        
    Returns:
        Modified Julian Date as float.
    """
    mjd_epoch = datetime(1858, 11, 17, tzinfo=timezone.utc)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    delta = dt - mjd_epoch
    return delta.total_seconds() / 86400.0


def jd_to_datetime(jd: float) -> datetime:
    """
    Convert Julian Date to datetime.
    
    Args:
        jd: Julian Date.
        
    Returns:
        datetime object in UTC.
    """
    # JD = MJD + 2400000.5
    mjd = jd - 2400000.5
    return mjd_to_datetime(mjd)


def datetime_to_jd(dt: datetime) -> float:
    """
    Convert datetime to Julian Date.
    
    Args:
        dt: datetime object.
        
    Returns:
        Julian Date as float.
    """
    mjd = datetime_to_mjd(dt)
    return mjd + 2400000.5


def utc_to_local(utc_dt: datetime, tz_offset_hours: float = 0) -> datetime:
    """
    Convert UTC datetime to local time.
    
    Args:
        utc_dt: UTC datetime.
        tz_offset_hours: Timezone offset in hours (e.g., -3 for BRT).
        
    Returns:
        Local datetime.
    """
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    from datetime import timedelta
    local_offset = timedelta(hours=tz_offset_hours)
    local_tz = timezone(local_offset)
    
    return utc_dt.astimezone(local_tz)


def format_mjd(mjd: float, precision: int = 5) -> str:
    """
    Format MJD as string.
    
    Args:
        mjd: Modified Julian Date.
        precision: Number of decimal places.
        
    Returns:
        Formatted MJD string.
    """
    return f"MJD {mjd:.{precision}f}"


def format_datetime(dt: datetime, include_time: bool = True) -> str:
    """
    Format datetime for display.
    
    Args:
        dt: datetime object.
        include_time: Include time in output.
        
    Returns:
        Formatted datetime string.
    """
    if include_time:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return dt.strftime("%Y-%m-%d")


def get_current_mjd() -> float:
    """
    Get current time as MJD.
    
    Returns:
        Current Modified Julian Date.
    """
    return datetime_to_mjd(datetime.now(timezone.utc))


def calculate_hour_angle(ra_deg: float, 
                        lst_hours: float) -> float:
    """
    Calculate hour angle from RA and local sidereal time.
    
    Args:
        ra_deg: Right ascension in degrees.
        lst_hours: Local sidereal time in hours.
        
    Returns:
        Hour angle in hours (-12 to +12).
    """
    ra_hours = ra_deg / 15.0
    ha = lst_hours - ra_hours
    
    # Normalize to -12 to +12 range
    while ha > 12:
        ha -= 24
    while ha < -12:
        ha += 24
    
    return ha


def is_object_observable(ra_deg: float, dec_deg: float,
                        lat_deg: float, lst_hours: float,
                        min_altitude: float = 30) -> bool:
    """
    Check if an object is observable from a given location.
    
    Args:
        ra_deg: Right ascension in degrees.
        dec_deg: Declination in degrees.
        lat_deg: Observatory latitude in degrees.
        lst_hours: Local sidereal time in hours.
        min_altitude: Minimum altitude in degrees.
        
    Returns:
        True if object is above minimum altitude.
    """
    import numpy as np
    
    ha_hours = calculate_hour_angle(ra_deg, lst_hours)
    ha_rad = np.radians(ha_hours * 15)
    dec_rad = np.radians(dec_deg)
    lat_rad = np.radians(lat_deg)
    
    # Calculate altitude
    sin_alt = (np.sin(dec_rad) * np.sin(lat_rad) + 
               np.cos(dec_rad) * np.cos(lat_rad) * np.cos(ha_rad))
    
    alt_deg = np.degrees(np.arcsin(sin_alt))
    
    return alt_deg >= min_altitude


def parse_iso_timestamp(timestamp: str) -> datetime:
    """
    Parse ISO format timestamp string.
    
    Args:
        timestamp: ISO format timestamp string.
        
    Returns:
        datetime object.
    """
    try:
        # Handle various ISO formats
        if 'Z' in timestamp:
            timestamp = timestamp.replace('Z', '+00:00')
        
        dt = datetime.fromisoformat(timestamp)
        
        # Convert to UTC if timezone-aware
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        
        return dt
    except Exception:
        return datetime.utcnow()


def calculate_age_hours(timestamp: str) -> float:
    """
    Calculate age of event in hours from timestamp.
    
    Args:
        timestamp: ISO format timestamp.
        
    Returns:
        Age in hours.
    """
    event_time = parse_iso_timestamp(timestamp)
    now = datetime.utcnow()
    
    age = now - event_time
    return max(0, age.total_seconds() / 3600)


# Import timedelta at module level
from datetime import timedelta
