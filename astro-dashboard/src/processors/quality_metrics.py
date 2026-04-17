"""
Quality Metrics - Calculates image and data quality metrics.

Computes FWHM, ellipticity, SNR, and other quality indicators for astronomical data.
"""

from typing import List, Dict, Any, Optional
import logging

import numpy as np
import pandas as pd
from astropy.stats import sigma_clipped_stats

from src.utils.logger import get_logger

logger = get_logger(__name__)


class QualityMetrics:
    """Calculates quality metrics for astronomical observations."""
    
    def __init__(self):
        """Initialize quality metrics calculator."""
        self.metrics_history: List[Dict[str, Any]] = []
        
    def calculate_fwhm(self, data: np.ndarray, 
                      pixel_scale: float = 0.4) -> float:
        """
        Calculate Full Width at Half Maximum from image data.
        
        Args:
            data: 2D array of pixel values (cutout around star).
            pixel_scale: Pixel scale in arcseconds/pixel.
            
        Returns:
            FWHM in arcseconds.
        """
        try:
            # Sigma-clipped statistics to remove outliers
            mean, median, std = sigma_clipped_stats(data, sigma=3.0)
            
            # Fit 2D Gaussian (simplified approach)
            # In production, would use photutils or similar
            
            # Find peak and estimate width
            max_val = np.max(data)
            half_max = max_val / 2
            
            # Find pixels above half max
            above_half = data > half_max
            indices = np.where(above_half)
            
            if len(indices[0]) < 4:
                return 99.0  # Bad measurement
            
            # Estimate FWHM from spread
            y_spread = np.max(indices[0]) - np.min(indices[0]) + 1
            x_spread = np.max(indices[1]) - np.min(indices[1]) + 1
            
            fwhm_pixels = np.sqrt(y_spread * x_spread)
            fwhm_arcsec = fwhm_pixels * pixel_scale
            
            return round(fwhm_arcsec, 2)
            
        except Exception as e:
            logger.warning(f"Error calculating FWHM: {e}")
            return 99.0
    
    def calculate_ellipticity(self, data: np.ndarray) -> float:
        """
        Calculate ellipticity of source.
        
        Args:
            data: 2D array of pixel values.
            
        Returns:
            Ellipticity (0=circular, 1=highly elongated).
        """
        try:
            # Calculate moments
            y, x = np.indices(data.shape)
            
            total_flux = np.sum(data)
            if total_flux == 0:
                return 1.0
            
            x_mean = np.sum(x * data) / total_flux
            y_mean = np.sum(y * data) / total_flux
            
            x_var = np.sum(((x - x_mean) ** 2) * data) / total_flux
            y_var = np.sum(((y - y_mean) ** 2) * data) / total_flux
            xy_cov = np.sum((x - x_mean) * (y - y_mean) * data) / total_flux
            
            # Eigenvalues of covariance matrix
            trace = x_var + y_var
            det = x_var * y_var - xy_cov ** 2
            
            if det <= 0:
                return 1.0
            
            lambda1 = (trace + np.sqrt(trace**2 - 4*det)) / 2
            lambda2 = (trace - np.sqrt(trace**2 - 4*det)) / 2
            
            if lambda2 <= 0:
                return 1.0
            
            # Ellipticity = 1 - b/a
            ellipticity = 1 - np.sqrt(lambda2 / lambda1)
            
            return round(max(0, min(1, ellipticity)), 3)
            
        except Exception as e:
            logger.warning(f"Error calculating ellipticity: {e}")
            return 1.0
    
    def calculate_snr(self, data: np.ndarray, 
                     aperture_radius: int = 5) -> float:
        """
        Calculate signal-to-noise ratio.
        
        Args:
            data: 2D array of pixel values.
            aperture_radius: Radius of aperture in pixels.
            
        Returns:
            SNR value.
        """
        try:
            # Simple aperture photometry
            y, x = np.indices(data.shape)
            center_y, center_x = data.shape[0] // 2, data.shape[1] // 2
            
            # Aperture mask
            r = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            aperture_mask = r <= aperture_radius
            
            # Background annulus
            bg_mask = (r > aperture_radius * 1.5) & (r <= aperture_radius * 3)
            
            if not np.any(bg_mask):
                bg_mask = ~aperture_mask
            
            # Calculate flux and noise
            source_flux = np.sum(data[aperture_mask])
            bg_mean, bg_median, bg_std = sigma_clipped_stats(data[bg_mask])
            
            n_pixels = np.sum(aperture_mask)
            noise = bg_std * np.sqrt(n_pixels)
            
            if noise == 0:
                return 0.0
            
            snr = source_flux / noise
            
            return round(max(0, snr), 1)
            
        except Exception as e:
            logger.warning(f"Error calculating SNR: {e}")
            return 0.0
    
    def calculate_seeing_quality(self, fwhm_values: List[float]) -> Dict[str, Any]:
        """
        Assess seeing quality from a series of FWHM measurements.
        
        Args:
            fwhm_values: List of FWHM measurements in arcseconds.
            
        Returns:
            Dictionary with seeing quality assessment.
        """
        if not fwhm_values:
            return {"status": "unknown", "fwhm_avg": None}
        
        fwhm_array = np.array(fwhm_values)
        fwhm_array = fwhm_array[fwhm_array < 10]  # Remove bad measurements
        
        if len(fwhm_array) == 0:
            return {"status": "unknown", "fwhm_avg": None}
        
        avg_fwhm = np.mean(fwhm_array)
        std_fwhm = np.std(fwhm_array)
        
        # Quality classification
        if avg_fwhm < 1.5:
            status = "excellent"
            color = "#00FF00"
        elif avg_fwhm < 2.5:
            status = "good"
            color = "#90EE90"
        elif avg_fwhm < 3.5:
            status = "fair"
            color = "#FFFF00"
        else:
            status = "poor"
            color = "#FF0000"
        
        return {
            "status": status,
            "color": color,
            "fwhm_avg": round(avg_fwhm, 2),
            "fwhm_std": round(std_fwhm, 2),
            "fwhm_min": round(np.min(fwhm_array), 2),
            "fwhm_max": round(np.max(fwhm_array), 2),
            "n_measurements": len(fwhm_array)
        }
    
    def calculate_image_quality_score(self, fwhm: float, ellipticity: float, 
                                      snr: float) -> float:
        """
        Calculate overall image quality score.
        
        Args:
            fwhm: FWHM in arcseconds.
            ellipticity: Ellipticity (0-1).
            snr: Signal-to-noise ratio.
            
        Returns:
            Quality score (0-100).
        """
        # Normalize each metric
        fwhm_score = max(0, 100 - (fwhm - 0.5) * 30)  # Best at 0.5"
        ellip_score = (1 - ellipticity) * 100  # Best at 0
        snr_score = min(100, snr * 2)  # Best at SNR > 50
        
        # Weighted average
        quality = 0.4 * fwhm_score + 0.3 * ellip_score + 0.3 * snr_score
        
        return round(max(0, min(100, quality)), 1)
    
    def analyze_catalog_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze quality metrics for a catalog DataFrame.
        
        Args:
            df: DataFrame with columns: fwhm, ellipticity, snr.
            
        Returns:
            Dictionary with quality analysis.
        """
        results = {}
        
        if "fwhm" in df.columns:
            fwhm_vals = df["fwhm"].dropna().values
            results["fwhm"] = {
                "mean": round(float(np.mean(fwhm_vals)), 2),
                "median": round(float(np.median(fwhm_vals)), 2),
                "std": round(float(np.std(fwhm_vals)), 2),
                "min": round(float(np.min(fwhm_vals)), 2),
                "max": round(float(np.max(fwhm_vals)), 2)
            }
        
        if "ellipticity" in df.columns:
            ellip_vals = df["ellipticity"].dropna().values
            results["ellipticity"] = {
                "mean": round(float(np.mean(ellip_vals)), 3),
                "median": round(float(np.median(ellip_vals)), 3),
                "std": round(float(np.std(ellip_vals)), 3)
            }
        
        if "snr" in df.columns:
            snr_vals = df["snr"].dropna().values
            results["snr"] = {
                "mean": round(float(np.mean(snr_vals)), 1),
                "median": round(float(np.median(snr_vals)), 1),
                "n_high_snr": int(np.sum(snr_vals > 20)),
                "n_low_snr": int(np.sum(snr_vals < 5))
            }
        
        # Overall quality assessment
        if all(k in results for k in ["fwhm", "ellipticity", "snr"]):
            avg_quality = self.calculate_image_quality_score(
                results["fwhm"]["median"],
                results["ellipticity"]["median"],
                results["snr"]["median"]
            )
            results["overall_quality_score"] = avg_quality
        
        return results
    
    def detect_quality_issues(self, df: pd.DataFrame, 
                             thresholds: Optional[Dict[str, float]] = None) -> List[Dict]:
        """
        Detect objects with quality issues.
        
        Args:
            df: DataFrame with quality metrics.
            thresholds: Custom threshold values.
            
        Returns:
            List of issue dictionaries.
        """
        default_thresholds = {
            "fwhm_max": 5.0,
            "ellipticity_max": 0.7,
            "snr_min": 3.0
        }
        
        if thresholds:
            default_thresholds.update(thresholds)
        
        issues = []
        
        # Check each row for issues
        for idx, row in df.iterrows():
            row_issues = []
            
            if "fwhm" in row and row["fwhm"] > default_thresholds["fwhm_max"]:
                row_issues.append(f"High FWHM: {row['fwhm']:.2f}\"")
            
            if "ellipticity" in row and row["ellipticity"] > default_thresholds["ellipticity_max"]:
                row_issues.append(f"High ellipticity: {row['ellipticity']:.3f}")
            
            if "snr" in row and row["snr"] < default_thresholds["snr_min"]:
                row_issues.append(f"Low SNR: {row['snr']:.1f}")
            
            if row_issues:
                issues.append({
                    "index": idx,
                    "id": row.get("id", idx),
                    "issues": row_issues
                })
        
        return issues
    
    def add_metric_to_history(self, metrics: Dict[str, Any]):
        """
        Add metrics to history for trend analysis.
        
        Args:
            metrics: Dictionary of metric values.
        """
        from datetime import datetime
        metrics["timestamp"] = datetime.utcnow().isoformat()
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def get_trend_analysis(self, metric_name: str, 
                          hours: int = 24) -> Dict[str, Any]:
        """
        Analyze trend for a specific metric.
        
        Args:
            metric_name: Name of metric to analyze.
            hours: Time window in hours.
            
        Returns:
            Dictionary with trend analysis.
        """
        if not self.metrics_history:
            return {"trend": "insufficient_data"}
        
        values = [m.get(metric_name) for m in self.metrics_history if m.get(metric_name) is not None]
        
        if len(values) < 2:
            return {"trend": "insufficient_data"}
        
        # Simple linear trend
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        if abs(slope) < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        return {
            "metric": metric_name,
            "trend": trend,
            "slope": round(slope, 4),
            "current": round(values[-1], 3),
            "avg": round(np.mean(values), 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3)
        }
