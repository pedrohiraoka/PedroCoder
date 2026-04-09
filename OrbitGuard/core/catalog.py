"""
Wrapper for astronomical catalog APIs.

This module provides unified access to NASA Exoplanet Archive,
JPL Horizons, Lightkurve, and Gaia via astroquery.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple, Union
from dataclasses import dataclass

from astropy.coordinates import SkyCoord, Angle
from astropy import units as u
from astropy.time import Time

try:
    from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
    from astroquery.jplhorizons import Horizons
    from astroquery.gaia import Gaia
    EXOPLANET_AVAILABLE = True
except ImportError:
    EXOPLANET_AVAILABLE = False
    NasaExoplanetArchive = None
    Horizons = None
    Gaia = None

try:
    import lightkurve as lk
    LIGHTKURVE_AVAILABLE = True
except ImportError:
    LIGHTKURVE_AVAILABLE = False
    lk = None

from utils.config import config
from utils.cache import cache_manager

logger = logging.getLogger(__name__)


@dataclass
class ExoplanetData:
    """Confirmed exoplanet information."""
    planet_name: str
    hostname: str
    ra: float
    dec: float
    period_days: float
    transit_depth_ppm: Optional[float]
    planet_radius_earth: Optional[float]
    stellar_mag: Optional[float]
    discovery_year: Optional[int]


@dataclass
class AsteroidData:
    """Asteroid ephemeris and identification data."""
    target_id: str
    ra: float
    dec: float
    ra_rate: float  # arcsec/hr
    dec_rate: float  # arcsec/hr
    v_mag: Optional[float]
    distance_au: Optional[float]
    constellation: Optional[str]


@dataclass
class StarCandidate:
    """Star candidate for occultation observations."""
    source_id: str
    ra: float
    dec: float
    g_mag: float
    bp_rp: Optional[float]
    parallax: Optional[float]
    has_exoplanet: bool
    exoplanet_count: int = 0


class CatalogAPI:
    """
    Unified interface for astronomical catalog queries.

    Provides methods to query exoplanets, asteroids, and stellar catalogs
    with built-in caching and error handling.
    """

    def __init__(self, use_cache: bool = True):
        """
        Initialize the catalog API wrapper.

        Args:
            use_cache: Enable/disable caching of API responses.
        """
        self.use_cache = use_cache
        self.exoplanet_archive = NasaExoplanetArchive() if EXOPLANET_AVAILABLE else None
        logger.info(f"CatalogAPI initialized - Exoplanet Archive: {EXOPLANET_AVAILABLE}, "
                   f"Lightkurve: {LIGHTKURVE_AVAILABLE}")

    def get_exoplanet_by_hostname(
        self, 
        hostname: str
    ) -> Optional[ExoplanetData]:
        """
        Retrieve confirmed exoplanet data by host star name.

        Args:
            hostname: Host star identifier (e.g., 'HD 209458', 'TIC 12345678').

        Returns:
            ExoplanetData if found, None otherwise.
        """
        if not EXOPLANET_AVAILABLE or self.exoplanet_archive is None:
            logger.error("NASA Exoplanet Archive not available")
            return None

        cache_key_params = {"hostname": hostname}
        
        if self.use_cache:
            cached = cache_manager.get("exoplanet_hostname", cache_key_params)
            if cached:
                logger.debug(f"Using cached exoplanet data for {hostname}")
                return ExoplanetData(**cached)

        try:
            # Query PSCompPars table (Planetary System Composite Parameters)
            table = self.exoplanet_archive.query_criteria(
                table='PSCompPars',
                hostname=hostname
            )
            
            if table is None or len(table) == 0:
                logger.info(f"No confirmed planets found for {hostname}")
                return None

            # Get first planet (most likely target)
            row = table[0]
            
            data = ExoplanetData(
                planet_name=row.get('pl_name', ''),
                hostname=row.get('hostname', hostname),
                ra=float(row.get('ra', 0)),
                dec=float(row.get('dec', 0)),
                period_days=float(row.get('pl_orbper', 0)),
                transit_depth_ppm=float(row.get('pl_trandep', None) or 0),
                planet_radius_earth=float(row.get('pl_rade', None) or 0),
                stellar_mag=float(row.get('st_mag', None) or 0),
                discovery_year=int(row.get('disc_year', 0) or 0)
            )

            if self.use_cache:
                cache_manager.set("exoplanet_hostname", cache_key_params, vars(data))

            return data

        except Exception as e:
            logger.error(f"Error querying exoplanet archive for {hostname}: {e}")
            return None

    def get_exoplanet_by_coords(
        self,
        ra: float,
        dec: float,
        radius_deg: float = 0.01
    ) -> Optional[ExoplanetData]:
        """
        Search for confirmed exoplanets near given coordinates.

        Args:
            ra: Right ascension in degrees.
            dec: Declination in degrees.
            radius_deg: Search radius in degrees.

        Returns:
            ExoplanetData if found, None otherwise.
        """
        if not EXOPLANET_AVAILABLE or self.exoplanet_archive is None:
            logger.error("NASA Exoplanet Archive not available")
            return None

        cache_key_params = {"ra": ra, "dec": dec, "radius": radius_deg}
        
        if self.use_cache:
            cached = cache_manager.get("exoplanet_coords", cache_key_params)
            if cached:
                return ExoplanetData(**cached)

        try:
            # Use PSCompPars table with coordinate search via ADQL where clause
            table = self.exoplanet_archive.query_criteria(
                table='PSCompPars',
                selectcols=['pl_name', 'hostname', 'ra', 'dec', 'pl_orbper', 
                           'pl_trandep', 'pl_rade', 'st_mag', 'disc_year'],
                where=f"ra BETWEEN {ra - radius_deg*3600} AND {ra + radius_deg*3600} "
                     f"AND dec BETWEEN {dec - radius_deg*3600} AND {dec + radius_deg*3600}"
            )

            if table is None or len(table) == 0:
                return None

            row = table[0]
            data = ExoplanetData(
                planet_name=row.get('pl_name', ''),
                hostname=row.get('hostname', ''),
                ra=float(row.get('ra', 0)),
                dec=float(row.get('dec', 0)),
                period_days=float(row.get('pl_orbper', 0)),
                transit_depth_ppm=float(row.get('pl_trandep', None) or 0),
                planet_radius_earth=float(row.get('pl_rade', None) or 0),
                stellar_mag=float(row.get('st_mag', None) or 0),
                discovery_year=int(row.get('disc_year', 0) or 0)
            )

            if self.use_cache:
                cache_manager.set("exoplanet_coords", cache_key_params, vars(data))

            return data

        except Exception as e:
            logger.error(f"Error querying exoplanet archive by coords: {e}")
            return None

    def get_asteroid_ephemeris(
        self,
        target_id: str,
        obs_time: Union[datetime, Time],
        observer_location: Optional[SkyCoord] = None
    ) -> Optional[AsteroidData]:
        """
        Get ephemeris for a specific asteroid at observation time.

        Args:
            target_id: Asteroid designation (e.g., 'Ceres', '1 Pallas', '2020 XL5').
            obs_time: Observation time (datetime or astropy Time).
            observer_location: Observer location (optional, defaults to geocentric).

        Returns:
            AsteroidData with position and motion information.
        """
        if not EXOPLANET_AVAILABLE:
            logger.error("astroquery not available")
            return None

        if isinstance(obs_time, datetime):
            obs_time = Time(obs_time)

        cache_key_params = {
            "target_id": target_id,
            "obs_time": obs_time.iso
        }

        if self.use_cache:
            cached = cache_manager.get("asteroid_ephem", cache_key_params)
            if cached:
                return AsteroidData(**cached)

        try:
            # Setup JPL Horizons query
            obj = Horizons(
                id=target_id,
                location='@sun',  # Heliocentric for basic ephemeris
                epochs=obs_time.jd
            )
            
            eph = obj.ephemerides(refplane='ecliptic')
            
            if len(eph) == 0:
                logger.warning(f"No ephemeris found for {target_id}")
                return None

            row = eph[0]
            data = AsteroidData(
                target_id=target_id,
                ra=float(row['RA']),
                dec=float(row['DEC']),
                ra_rate=float(row.get('RA_rate', 0)),
                dec_rate=float(row.get('DEC_rate', 0)),
                v_mag=float(row.get('V', None) or 0),
                distance_au=float(row.get('r', None) or 0),
                constellation=row.get('Constellation', '')
            )

            if self.use_cache:
                cache_manager.set("asteroid_ephem", cache_key_params, vars(data))

            return data

        except Exception as e:
            logger.error(f"Error getting ephemeris for {target_id}: {e}")
            return None

    def search_asteroids_in_field(
        self,
        ra: float,
        dec: float,
        obs_time: Union[datetime, Time],
        fov_deg: float = 1.0
    ) -> List[AsteroidData]:
        """
        Search for asteroids within a field of view at observation time.

        Args:
            ra: Field center RA in degrees.
            dec: Field center DEC in degrees.
            obs_time: Observation time.
            fov_deg: Field of view diameter in degrees.

        Returns:
            List of AsteroidData for asteroids in the field.
        """
        if not EXOPLANET_AVAILABLE:
            return []

        if isinstance(obs_time, datetime):
            obs_time = Time(obs_time)

        # Note: This is a simplified implementation
        # In production, would query MPC database for numbered asteroids
        logger.info(f"Searching asteroids in {fov_deg}° field at ({ra}, {dec})")
        
        # For MVP, we'll return empty list with log message
        # Full implementation would use astroquery.mpc or pre-loaded catalog
        return []

    def get_lightcurve(
        self,
        target: str,
        mission: str = "TESS"
    ) -> Optional[Any]:
        """
        Search for and retrieve light curve data.

        Args:
            target: Target identifier (TIC, KIC, etc.).
            mission: Mission name ('TESS', 'Kepler', 'K2').

        Returns:
            LightCurve object or None if not found.
        """
        if not LIGHTKURVE_AVAILABLE or lk is None:
            logger.warning("Lightkurve not available")
            return None

        cache_key_params = {"target": target, "mission": mission}

        if self.use_cache:
            # Note: LightCurve objects aren't easily serializable
            # Cache metadata only, fetch actual data
            pass

        try:
            if mission.upper() == "TESS":
                search_result = lk.search_tess_lightcurves(target)
            elif mission.upper() == "KEPLER":
                search_result = lk.search_kepler_lightcurves(target)
            elif mission.upper() == "K2":
                search_result = lk.search_k2_lightcurves(target)
            else:
                logger.error(f"Unknown mission: {mission}")
                return None

            if len(search_result) == 0:
                logger.info(f"No light curves found for {target}")
                return None

            # Download first result
            lightcurve = search_result.download()
            logger.info(f"Retrieved light curve with {len(lightcurve)} points")
            return lightcurve

        except Exception as e:
            logger.error(f"Error retrieving light curve for {target}: {e}")
            return None

    def query_gaia_stars(
        self,
        ra: float,
        dec: float,
        radius_deg: float = 0.1,
        magnitude_limit: float = 20.0
    ) -> List[StarCandidate]:
        """
        Query Gaia DR3 for stars in a region.

        Args:
            ra: Center RA in degrees.
            dec: Center DEC in degrees.
            radius_deg: Search radius in degrees.
            magnitude_limit: Maximum G magnitude.

        Returns:
            List of StarCandidate objects.
        """
        if not EXOPLANET_AVAILABLE:
            return []

        cache_key_params = {
            "ra": ra,
            "dec": dec,
            "radius": radius_deg,
            "mag_limit": magnitude_limit
        }

        if self.use_cache:
            cached = cache_manager.get("gaia_stars", cache_key_params)
            if cached:
                return [StarCandidate(**s) for s in cached]

        try:
            # ADQL query for Gaia
            query = f"""
                SELECT TOP 1000
                    source_id,
                    ra,
                    dec,
                    phot_g_mean_mag as g_mag,
                    bp_rp,
                    parallax
                FROM gaiadr3.gaia_source
                WHERE 1 = CONTAINS(
                    POINT('ICRS', ra, dec),
                    CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
                )
                AND phot_g_mean_mag < {magnitude_limit}
            """

            job = Gaia.launch_job_async(query)
            results = job.get_results()

            stars = []
            for row in results:
                stars.append(StarCandidate(
                    source_id=str(row['source_id']),
                    ra=float(row['ra']),
                    dec=float(row['dec']),
                    g_mag=float(row['g_mag']),
                    bp_rp=float(row['bp_rp'] if row['bp_rp'] is not None else 0),
                    parallax=float(row['parallax'] if row['parallax'] is not None else 0),
                    has_exoplanet=False  # Will be updated by cross-match
                ))

            if self.use_cache:
                cache_manager.set("gaia_stars", cache_key_params, [vars(s) for s in stars])

            logger.info(f"Found {len(stars)} Gaia stars")
            return stars

        except Exception as e:
            logger.error(f"Error querying Gaia: {e}")
            return []

    def check_star_has_exoplanet(
        self,
        ra: float,
        dec: float,
        tolerance_arcsec: float = 3.0
    ) -> Tuple[bool, int]:
        """
        Check if a star position matches a known exoplanet host.

        Args:
            ra: Star RA in degrees.
            dec: Star DEC in degrees.
            tolerance_arcsec: Matching tolerance.

        Returns:
            Tuple of (has_exoplanet, count).
        """
        if not EXOPLANET_AVAILABLE or self.exoplanet_archive is None:
            return False, 0

        try:
            # Convert tolerance to degrees
            tolerance_deg = tolerance_arcsec / 3600.0
            
            # Use PSCompPars table with coordinate search
            table = self.exoplanet_archive.query_criteria(
                table='PSCompPars',
                selectcols=['pl_name', 'hostname'],
                where=f"ra BETWEEN {ra - tolerance_deg} AND {ra + tolerance_deg} "
                     f"AND dec BETWEEN {dec - tolerance_deg} AND {dec + tolerance_deg}"
            )

            if table is None or len(table) == 0:
                return False, 0

            # Count unique hostnames
            hostnames = set(table['hostname'])
            return True, len(hostnames)

        except Exception as e:
            logger.error(f"Error checking exoplanet match: {e}")
            return False, 0


# Global API instance
catalog_api = CatalogAPI(use_cache=True)
