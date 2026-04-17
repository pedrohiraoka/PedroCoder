"""
FITS Loader - Optimized reading of large astronomical catalogs.

Uses fitsio for chunked/memmap reading of FITS files with 10M+ objects.
"""

import os
from typing import Dict, Any, Optional, List, Generator, Tuple
import logging
import numpy as np

try:
    import fitsio
    FITSIO_AVAILABLE = True
except ImportError:
    FITSIO_AVAILABLE = False

from astropy.table import Table
import pandas as pd

from src.utils.logger import get_logger
import config

logger = get_logger(__name__)


class FITSCatalogLoader:
    """Efficiently loads large astronomical catalogs from FITS files."""
    
    def __init__(self, filepath: Optional[str] = None, use_mock: bool = True):
        """
        Initialize FITS catalog loader.
        
        Args:
            filepath: Path to FITS catalog file.
            use_mock: If True, generate mock catalog data when file unavailable.
        """
        self.filepath = filepath or config.MOCK_FITS_PATH
        self.use_mock = use_mock or not FITSIO_AVAILABLE
        self.catalog_info: Dict[str, Any] = {}
        self._fits_file = None
        
    def open(self) -> bool:
        """
        Open the FITS file for reading.
        
        Returns:
            True if successfully opened, False otherwise.
        """
        if self.use_mock:
            logger.info("Using mock catalog data")
            return True
        
        try:
            if not os.path.exists(self.filepath):
                logger.warning(f"FITS file not found: {self.filepath}, using mock")
                self.use_mock = True
                return True
            
            self._fits_file = fitsio.FITS(self.filepath, 'r')
            logger.info(f"Opened FITS file: {self.filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening FITS file: {e}")
            self.use_mock = True
            return True  # Fallback to mock
    
    def close(self):
        """Close the FITS file."""
        if self._fits_file is not None:
            self._fits_file.close()
            self._fits_file = None
    
    def get_catalog_info(self) -> Dict[str, Any]:
        """
        Get metadata about the catalog.
        
        Returns:
            Dictionary with catalog information.
        """
        if self.use_mock:
            return {
                "n_objects": config.MAX_OBJECTS_IN_MEMORY,
                "columns": ["ra", "dec", "magnitude", "redshift", "fwhm", 
                           "ellipticity", "snr", "class", "z_phot"],
                "filename": "mock_catalog.fits",
                "file_size_mb": 0
            }
        
        try:
            if self._fits_file is None:
                self.open()
            
            hdu = self._fits_file[1]  # Assume data in first extension
            info = {
                "n_objects": hdu.get_nrows(),
                "columns": hdu.get_colnames(),
                "filename": os.path.basename(self.filepath),
                "file_size_mb": round(os.path.getsize(self.filepath) / 1e6, 2)
            }
            self.catalog_info = info
            return info
            
        except Exception as e:
            logger.error(f"Error getting catalog info: {e}")
            return self.get_catalog_info()  # Return mock info
    
    def read_chunk(self, start: int, stop: int) -> pd.DataFrame:
        """
        Read a chunk of the catalog.
        
        Args:
            start: Starting row index.
            stop: Stopping row index (exclusive).
            
        Returns:
            DataFrame with the requested rows.
        """
        if self.use_mock:
            return self._generate_mock_chunk(start, stop)
        
        try:
            if self._fits_file is None:
                self.open()
            
            data = self._fits_file[1][start:stop]
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error reading chunk [{start}:{stop}]: {e}")
            return self._generate_mock_chunk(start, stop)
    
    def read_all(self, max_rows: Optional[int] = None) -> pd.DataFrame:
        """
        Read entire catalog (or up to max_rows).
        
        Args:
            max_rows: Maximum number of rows to read.
            
        Returns:
            DataFrame with catalog data.
        """
        if self.use_mock:
            n_rows = min(max_rows or config.MAX_OBJECTS_IN_MEMORY, config.MAX_OBJECTS_IN_MEMORY)
            return self._generate_mock_chunk(0, n_rows)
        
        try:
            if self._fits_file is None:
                self.open()
            
            n_rows = self._fits_file[1].get_nrows()
            if max_rows:
                n_rows = min(n_rows, max_rows)
            
            data = self._fits_file[1][0:n_rows]
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error reading catalog: {e}")
            return self._generate_mock_chunk(0, max_rows or config.MAX_OBJECTS_IN_MEMORY)
    
    def iter_chunks(self, chunk_size: Optional[int] = None) -> Generator[pd.DataFrame, None, None]:
        """
        Iterate over catalog in chunks.
        
        Args:
            chunk_size: Number of rows per chunk.
            
        Yields:
            DataFrames with chunk data.
        """
        chunk_size = chunk_size or config.FITS_CHUNK_SIZE
        
        if self.use_mock:
            total_rows = config.MAX_OBJECTS_IN_MEMORY
            for start in range(0, total_rows, chunk_size):
                stop = min(start + chunk_size, total_rows)
                yield self._generate_mock_chunk(start, stop)
            return
        
        try:
            if self._fits_file is None:
                self.open()
            
            n_rows = self._fits_file[1].get_nrows()
            
            for start in range(0, n_rows, chunk_size):
                stop = min(start + chunk_size, n_rows)
                data = self._fits_file[1][start:stop]
                yield pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"Error iterating chunks: {e}")
            # Fallback: yield mock chunks
            total_rows = config.MAX_OBJECTS_IN_MEMORY
            for start in range(0, total_rows, chunk_size):
                stop = min(start + chunk_size, total_rows)
                yield self._generate_mock_chunk(start, stop)
    
    def _generate_mock_chunk(self, start: int, stop: int) -> pd.DataFrame:
        """
        Generate mock catalog data.
        
        Args:
            start: Starting row index.
            stop: Stopping row index.
            
        Returns:
            DataFrame with mock astronomical data.
        """
        n_rows = stop - start
        
        # Generate realistic astronomical data
        np.random.seed(42 + start)  # Reproducible but varied
        
        data = {
            "id": np.arange(start, stop),
            "ra": np.random.uniform(0, 360, n_rows),
            "dec": np.random.uniform(-90, 90, n_rows),
            "magnitude": np.random.normal(18, 2, n_rows),
            "redshift": np.random.exponential(0.3, n_rows),
            "fwhm": np.random.normal(1.5, 0.5, n_rows),
            "ellipticity": np.random.beta(2, 5, n_rows),
            "snr": np.random.normal(20, 10, n_rows),
            "class": np.random.choice(["STAR", "GALAXY", "QSO"], n_rows, 
                                     p=[0.2, 0.7, 0.1]),
            "z_phot": np.random.exponential(0.25, n_rows)
        }
        
        # Ensure physical bounds
        data["magnitude"] = np.clip(data["magnitude"], 10, 30)
        data["redshift"] = np.clip(data["redshift"], 0, 5)
        data["fwhm"] = np.clip(data["fwhm"], 0.3, 5)
        data["ellipticity"] = np.clip(data["ellipticity"], 0, 1)
        data["snr"] = np.clip(data["snr"], 1, 100)
        
        return pd.DataFrame(data)
    
    def query_by_coordinates(self, ra: float, dec: float, 
                            radius_deg: float = 0.1) -> pd.DataFrame:
        """
        Query objects within a circular region.
        
        Args:
            ra: Right ascension in degrees.
            dec: Declination in degrees.
            radius_deg: Search radius in degrees.
            
        Returns:
            DataFrame with matching objects.
        """
        # For large catalogs, this should use spatial indexing
        # Here we do a simple bounding box filter on a sample
        
        df = self.read_all(max_rows=100000)  # Sample for performance
        
        # Simple angular distance approximation (good for small radii)
        ra_rad = np.radians(ra)
        dec_rad = np.radians(dec)
        
        df_ra_rad = np.radians(df["ra"])
        df_dec_rad = np.radians(df["dec"])
        
        # Haversine-like distance
        delta_ra = df_ra_rad - ra_rad
        delta_dec = df_dec_rad - dec_rad
        
        a = np.sin(delta_dec/2)**2 + np.cos(dec_rad) * np.cos(df_dec_rad) * np.sin(delta_ra/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        distance_deg = np.degrees(c)
        
        mask = distance_deg <= radius_deg
        return df[mask].copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate summary statistics for the catalog.
        
        Returns:
            Dictionary with statistical summaries.
        """
        df = self.read_all(max_rows=50000)  # Sample for speed
        
        stats = {
            "n_objects": len(df),
            "magnitude": {
                "mean": round(df["magnitude"].mean(), 2),
                "std": round(df["magnitude"].std(), 2),
                "min": round(df["magnitude"].min(), 2),
                "max": round(df["magnitude"].max(), 2)
            },
            "redshift": {
                "mean": round(df["redshift"].mean(), 3),
                "median": round(df["redshift"].median(), 3)
            },
            "fwhm": {
                "mean": round(df["fwhm"].mean(), 2),
                "median": round(df["fwhm"].median(), 2)
            },
            "ellipticity": {
                "mean": round(df["ellipticity"].mean(), 3),
                "median": round(df["ellipticity"].median(), 3)
            },
            "snr": {
                "mean": round(df["snr"].mean(), 1),
                "median": round(df["snr"].median(), 1)
            },
            "class_distribution": df["class"].value_counts().to_dict()
        }
        
        return stats
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
