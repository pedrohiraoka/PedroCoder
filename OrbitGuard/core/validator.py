"""
Transit validation module for detecting false positives.

This module implements Module 1: Validador de Trânsito (Falsos Positivos).
It cross-matches exoplanet transit observations with asteroid positions
to identify potential false positive signals.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Any, Union, Literal
from dataclasses import dataclass, field
from enum import Enum

from astropy.coordinates import SkyCoord, Angle
from astropy import units as u
from astropy.time import Time

from core.catalog import CatalogAPI, ExoplanetData, AsteroidData, catalog_api
from utils.config import config

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation result status."""
    GREEN = "GREEN"  # No contamination detected
    YELLOW = "YELLOW"  # Potential contamination, review needed
    RED = "RED"  # High probability of false positive


@dataclass
class ContaminantInfo:
    """Information about a potential contaminating object."""
    object_id: str
    object_type: str  # 'asteroid', 'comet', 'background_star'
    ra: float
    dec: float
    separation_arcsec: float
    magnitude: Optional[float]
    proper_motion_mas_yr: Optional[float] = None


@dataclass
class ValidationResult:
    """Result of transit validation analysis."""
    status: ValidationStatus
    target_hostname: str
    target_ra: float
    target_dec: float
    obs_time_utc: datetime
    exoplanet_data: Optional[ExoplanetData]
    contaminants: List[ContaminantInfo] = field(default_factory=list)
    lightcurve_available: bool = False
    lightcurve_url: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "target_hostname": self.target_hostname,
            "target_ra": self.target_ra,
            "target_dec": self.target_dec,
            "obs_time_utc": self.obs_time_utc.isoformat(),
            "exoplanet_confirmed": self.exoplanet_data is not None,
            "planet_name": self.exoplanet_data.planet_name if self.exoplanet_data else None,
            "contaminant_count": len(self.contaminants),
            "contaminants": [
                {
                    "object_id": c.object_id,
                    "object_type": c.object_type,
                    "separation_arcsec": c.separation_arcsec,
                    "magnitude": c.magnitude
                }
                for c in self.contaminants
            ],
            "lightcurve_available": self.lightcurve_available,
            "lightcurve_url": self.lightcurve_url,
            "notes": self.notes
        }


class TransitValidator:
    """
    Validates exoplanet transit observations for false positives.

    Cross-matches target coordinates with asteroid ephemerides and
    background sources to identify potential contamination.
    """

    def __init__(self, api: Optional[CatalogAPI] = None):
        """
        Initialize the transit validator.

        Args:
            api: CatalogAPI instance. Uses global instance if None.
        """
        self.api = api or catalog_api
        self.search_radius_arcsec = config.DEFAULT_SEARCH_RADIUS_ARCSEC
        self.fov_deg = config.DEFAULT_FOV_DEG

    def validate_by_hostname(
        self,
        hostname: str,
        obs_time: Union[datetime, str],
        check_asteroids: bool = True
    ) -> ValidationResult:
        """
        Validate a transit observation by host star name.

        Args:
            hostname: Host star identifier.
            obs_time: Observation time (datetime or ISO string).
            check_asteroids: Whether to check for asteroid contamination.

        Returns:
            ValidationResult with validation status and details.
        """
        # Parse observation time
        if isinstance(obs_time, str):
            obs_time = datetime.fromisoformat(obs_time.replace('Z', '+00:00'))

        logger.info(f"Validating transit for {hostname} at {obs_time}")

        # Step 1: Get exoplanet data
        exoplanet_data = self.api.get_exoplanet_by_hostname(hostname)

        if exoplanet_data is None:
            return ValidationResult(
                status=ValidationStatus.YELLOW,
                target_hostname=hostname,
                target_ra=0.0,
                target_dec=0.0,
                obs_time_utc=obs_time,
                exoplanet_data=None,
                notes=[f"No confirmed exoplanet found for {hostname}"]
            )

        # Step 2: Validate using coordinates
        return self.validate_by_coords(
            ra=exoplanet_data.ra,
            dec=exoplanet_data.dec,
            obs_time=obs_time,
            exoplanet_data=exoplanet_data,
            check_asteroids=check_asteroids
        )

    def validate_by_coords(
        self,
        ra: float,
        dec: float,
        obs_time: Union[datetime, str],
        exoplanet_data: Optional[ExoplanetData] = None,
        check_asteroids: bool = True
    ) -> ValidationResult:
        """
        Validate a transit observation by coordinates.

        Args:
            ra: Right ascension in degrees.
            dec: Declination in degrees.
            obs_time: Observation time.
            exoplanet_data: Pre-fetched exoplanet data (optional).
            check_asteroids: Whether to check for asteroid contamination.

        Returns:
            ValidationResult with validation status and details.
        """
        # Parse observation time
        if isinstance(obs_time, str):
            obs_time = datetime.fromisoformat(obs_time.replace('Z', '+00:00'))

        hostname = exoplanet_data.hostname if exoplanet_data else f"J{ra:07.1f}{dec:+08.1f}"
        logger.info(f"Validating transit at ({ra}, {dec}) at {obs_time}")

        contaminants: List[ContaminantInfo] = []
        notes: List[str] = []

        # Step 1: Check for asteroid contamination
        if check_asteroids:
            asteroid_contaminants = self._check_asteroid_contamination(
                ra=ra,
                dec=dec,
                obs_time=obs_time
            )
            contaminants.extend(asteroid_contaminants)
            if asteroid_contaminants:
                notes.append(f"Found {len(asteroid_contaminants)} potential asteroid contaminant(s)")

        # Step 2: Try to get light curve
        lightcurve_available = False
        lightcurve_url = None

        if exoplanet_data and exoplanet_data.hostname:
            tic_match = self._extract_tic_id(exoplanet_data.hostname)
            if tic_match:
                lightcurve = self.api.get_lightcurve(tic_match, mission="TESS")
                if lightcurve is not None:
                    lightcurve_available = True
                    lightcurve_url = f"https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html?searchText={tic_match}"
                    notes.append("TESS light curve available")

        # Step 3: Determine validation status
        status = self._determine_status(contaminants, exoplanet_data)

        return ValidationResult(
            status=status,
            target_hostname=hostname,
            target_ra=ra,
            target_dec=dec,
            obs_time_utc=obs_time,
            exoplanet_data=exoplanet_data,
            contaminants=contaminants,
            lightcurve_available=lightcurve_available,
            lightcurve_url=lightcurve_url,
            notes=notes
        )

    def _check_asteroid_contamination(
        self,
        ra: float,
        dec: float,
        obs_time: datetime
    ) -> List[ContaminantInfo]:
        """
        Check for asteroid contamination in the field.

        Args:
            ra: Target RA in degrees.
            dec: Target DEC in degrees.
            obs_time: Observation time.

        Returns:
            List of ContaminantInfo for asteroids within search radius.
        """
        contaminants = []
        target_coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)

        # Search for asteroids in the field
        # Note: Full implementation would query MPC catalog
        # For MVP, we demonstrate with known bright asteroids
        
        # Example: Check some bright asteroids that might be in the field
        bright_asteroids = ['1 Ceres', '2 Pallas', '4 Vesta', '10 Hygiea']
        
        for asteroid_id in bright_asteroids:
            try:
                asteroid_data = self.api.get_asteroid_ephemeris(
                    target_id=asteroid_id,
                    obs_time=obs_time
                )

                if asteroid_data is None:
                    continue

                # Calculate angular separation
                asteroid_coord = SkyCoord(
                    ra=asteroid_data.ra*u.deg,
                    dec=asteroid_data.dec*u.deg
                )
                
                separation = target_coord.separation(asteroid_coord).arcsec

                if separation < self.search_radius_arcsec:
                    contaminants.append(ContaminantInfo(
                        object_id=asteroid_id,
                        object_type='asteroid',
                        ra=asteroid_data.ra,
                        dec=asteroid_data.dec,
                        separation_arcsec=separation,
                        magnitude=asteroid_data.v_mag,
                        proper_motion_mas_yr=None  # Would calculate from rates
                    ))
                    logger.warning(
                        f"Asteroid {asteroid_id} within {separation:.2f} arcsec of target"
                    )

            except Exception as e:
                logger.debug(f"Error checking asteroid {asteroid_id}: {e}")
                continue

        return contaminants

    def _determine_status(
        self,
        contaminants: List[ContaminantInfo],
        exoplanet_data: Optional[ExoplanetData]
    ) -> ValidationStatus:
        """
        Determine validation status based on contaminants and exoplanet data.

        Args:
            contaminants: List of detected contaminants.
            exoplanet_data: Exoplanet information.

        Returns:
            ValidationStatus enum value.
        """
        # No confirmed planet
        if exoplanet_data is None:
            return ValidationStatus.YELLOW

        # Critical contamination
        critical_contaminants = [
            c for c in contaminants 
            if c.separation_arcsec < config.MIN_SEPARATION_CRITICAL_ARCSEC
        ]
        
        if critical_contaminants:
            return ValidationStatus.RED

        # Warning-level contamination
        warning_contaminants = [
            c for c in contaminants
            if c.separation_arcsec < config.MIN_SEPARATION_WARNING_ARCSEC
        ]

        if warning_contaminants:
            return ValidationStatus.YELLOW

        # Check magnitude difference
        # If contaminant is much brighter, could still be problematic
        for c in contaminants:
            if c.magnitude and exoplanet_data.stellar_mag:
                if c.magnitude < exoplanet_data.stellar_mag - 2:
                    return ValidationStatus.YELLOW

        return ValidationStatus.GREEN

    def _extract_tic_id(self, hostname: str) -> Optional[str]:
        """
        Extract TIC ID from hostname for light curve search.

        Args:
            hostname: Host star identifier.

        Returns:
            TIC ID string or None.
        """
        import re
        
        # Match patterns like "TIC 123456789" or "2MASS J..."
        tic_match = re.search(r'TIC\s+(\d+)', hostname, re.IGNORECASE)
        if tic_match:
            return f"TIC {tic_match.group(1)}"
        
        # Try direct TIC prefix
        if hostname.upper().startswith('TIC'):
            return hostname
        
        return None


def validate_transit(
    target: str,
    obs_time: Union[datetime, str],
    use_coords: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to validate a transit observation.

    Args:
        target: Hostname or coordinate string.
        obs_time: Observation time.
        use_coords: If True, interpret target as coordinates.

    Returns:
        Dictionary with validation results.
    """
    validator = TransitValidator()

    if use_coords:
        # Parse coordinate string "RA,DEC"
        parts = target.split(',')
        if len(parts) != 2:
            return {"error": "Invalid coordinate format. Use 'RA,DEC'"}
        
        try:
            ra = float(parts[0].strip())
            dec = float(parts[1].strip())
        except ValueError:
            return {"error": "Could not parse coordinates as floats"}

        result = validator.validate_by_coords(ra=ra, dec=dec, obs_time=obs_time)
    else:
        result = validator.validate_by_hostname(hostname=target, obs_time=obs_time)

    return result.to_dict()
