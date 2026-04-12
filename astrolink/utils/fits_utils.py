"""
FITS file utilities for AstroLink.

Provides functions for creating sample FITS files for testing,
and other FITS-related utilities.
"""

import numpy as np
from pathlib import Path


def create_sample_fits(output_dir: str = None):
    """
    Create sample FITS files for testing the application.
    
    Args:
        output_dir: Directory to save files (default: astrolink/data/sample)
    """
    try:
        from astropy.io import fits
    except ImportError:
        print("astropy not available, cannot create sample FITS files")
        return []
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "sample"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    
    # Create bias frame (constant offset + noise)
    bias_data = np.ones((100, 100)) * 500 + np.random.normal(0, 5, (100, 100))
    bias_hdu = fits.PrimaryHDU(bias_data.astype(np.float32))
    bias_hdu.header['OBJECT'] = 'BIAS'
    bias_hdu.header['EXPTIME'] = 0
    bias_file = output_dir / "bias.fits"
    bias_hdu.writeto(bias_file, overwrite=True)
    created_files.append(str(bias_file))
    
    # Create dark frame (thermal signal + noise)
    y, x = np.ogrid[:100, :100]
    dark_data = np.ones((100, 100)) * 100 + np.random.normal(0, 10, (100, 100))
    dark_hdu = fits.PrimaryHDU(dark_data.astype(np.float32))
    dark_hdu.header['OBJECT'] = 'DARK'
    dark_hdu.header['EXPTIME'] = 60
    dark_file = output_dir / "dark.fits"
    dark_hdu.writeto(dark_file, overwrite=True)
    created_files.append(str(dark_file))
    
    # Create flat field (vignetting pattern)
    xx, yy = np.meshgrid(np.linspace(-1, 1, 100), np.linspace(-1, 1, 100))
    flat_data = 1.0 - 0.3 * (xx**2 + yy**2) + np.random.normal(0, 0.01, (100, 100))
    flat_data = flat_data / flat_data.mean() * 10000
    flat_hdu = fits.PrimaryHDU(flat_data.astype(np.float32))
    flat_hdu.header['OBJECT'] = 'FLAT'
    flat_hdu.header['EXPTIME'] = 10
    flat_file = output_dir / "flat.fits"
    flat_hdu.writeto(flat_file, overwrite=True)
    created_files.append(str(flat_file))
    
    # Create science frame (stars + background)
    science_data = np.random.normal(100, 10, (100, 100)).astype(np.float32)
    
    # Add some fake stars
    stars = [
        (30, 30, 500),
        (70, 50, 800),
        (50, 70, 300),
        (20, 80, 400),
        (80, 20, 600),
    ]
    
    for sx, sy, flux in stars:
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                if 0 <= sy+dy < 100 and 0 <= sx+dx < 100:
                    r = np.sqrt(dx**2 + dy**2)
                    science_data[sy+dy, sx+dx] += flux * np.exp(-r**2 / 4)
    
    science_hdu = fits.PrimaryHDU(science_data.astype(np.float32))
    science_hdu.header['OBJECT'] = 'TEST_FIELD'
    science_hdu.header['EXPTIME'] = 300
    science_hdu.header['RA'] = 180.0
    science_hdu.header['DEC'] = 45.0
    science_file = output_dir / "science.fits"
    science_hdu.writeto(science_file, overwrite=True)
    created_files.append(str(science_file))
    
    print(f"Created {len(created_files)} sample FITS files in {output_dir}")
    return created_files


if __name__ == "__main__":
    create_sample_fits()
