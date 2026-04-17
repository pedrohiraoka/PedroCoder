"""
Configuration file for AstroWatch & Triage Dashboard.

Contains observatory coordinates, operational limits, and mock data paths.
"""

# Observatory Configuration
OBSERVATORY_NAME = "Observatório Nacional"
OBSERVATORY_LAT = -22.9068  # degrees (Rio de Janeiro)
OBSERVATORY_LON = -43.2356  # degrees
OBSERVATORY_ELEVATION = 517  # meters

# Operational Limits
SEEING_GOOD_THRESHOLD = 1.5  # arcseconds
SEEING_BAD_THRESHOLD = 3.0  # arcseconds
HUMIDITY_ALERT_THRESHOLD = 85  # percent
WIND_SPEED_ALERT_THRESHOLD = 40  # km/h
TEMP_CCD_MAX = -100  # Celsius (warning if warmer)

# Polling Intervals (seconds)
VOEVENT_POLL_INTERVAL = 60
WEATHER_POLL_INTERVAL = 30
INSTRUMENT_POLL_INTERVAL = 10
QUALITY_UPDATE_INTERVAL = 5

# Mock Data Paths
MOCK_FITS_PATH = "data/mock_catalog.fits"
MOCK_WEATHER_DATA = True  # Use simulated weather data
MOCK_INSTRUMENT_DATA = True  # Use simulated instrument status

# Alert Priority Colors
PRIORITY_COLORS = {
    "GRB": "#FF0000",      # Red - Gamma Ray Burst (highest priority)
    "SN": "#FFA500",       # Orange - Supernova
    "Asteroid": "#FFFF00", # Yellow - Near Earth Object
    "Unknown": "#00FFFF",  # Cyan - Unknown transient
    "Normal": "#00FF00"    # Green - Normal events
}

# Dashboard Theme
DARK_THEME = {
    "background": "#0d1117",
    "card_bg": "#161b22",
    "text": "#c9d1d9",
    "text_secondary": "#8b949e",
    "border": "#30363d",
    "accent": "#58a6ff",
    "success": "#2ea043",
    "warning": "#d29922",
    "danger": "#da3633"
}

# FITS Catalog Configuration
FITS_CHUNK_SIZE = 100000  # Number of rows to read at once
MAX_OBJECTS_IN_MEMORY = 500000  # Limit for interactive visualization

# Export Formats
EXPORT_FORMATS = ["CSV", "JSON", "VOTable"]

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
