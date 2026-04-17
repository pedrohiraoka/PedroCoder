# AstroWatch & Triage Dashboard

A unified web dashboard for real-time astronomical alert monitoring, instrument status tracking, and interactive data quality triage.

![Dashboard](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-green)

## 🌟 Features

### Real-Time Monitoring
- **VOEvent Alert Polling**: Automatic fetching of astronomical transients (GRBs, Supernovae, Asteroids) every 60 seconds
- **Weather Conditions**: Seeing, humidity, wind speed, temperature, and cloud cover monitoring
- **Instrument Status**: CCD temperatures, shutter state, filter wheels, guiding, spectrograph status
- **Observing Conditions**: Go/No-Go recommendations based on combined weather and instrument health

### Data Quality Triage
- **Optimized FITS Loading**: Chunked reading of large catalogs (10M+ objects) via fitsio memmap
- **Quality Metrics**: FWHM, ellipticity, SNR calculations with statistical summaries
- **Linked Brushing**: Glue-inspired cross-filtering between sky map, magnitude-redshift, and quality plots
- **Export Functionality**: Download selected targets as CSV, JSON, or VOTable

## 📁 Project Structure

```
astro-dashboard/
├── app.py                      # Main Dash application entry point
├── config.py                   # Configuration constants and paths
├── requirements.txt            # Python dependencies
│
├── src/
│   ├── data_fetchers/
│   │   ├── voevent_fetcher.py  # VOEvent/TNS alert polling
│   │   ├── weather_fetcher.py  # Environmental conditions
│   │   ├── instrument_status.py# Telescope/detector health
│   │   └── fits_loader.py      # Optimized FITS catalog loading
│   │
│   ├── processors/
│   │   ├── alert_parser.py     # Alert filtering and prioritization
│   │   ├── quality_metrics.py  # FWHM, ellipticity, SNR calculations
│   │   └── data_aggregator.py  # Statistical aggregations
│   │
│   ├── visualizations/
│   │   ├── alert_map.py        # Sky maps and alert charts
│   │   ├── status_panels.py    # Instrument/weather cards
│   │   └── linked_views.py     # Cross-filtered plots
│   │
│   └── utils/
│       ├── logger.py           # Structured logging
│       └── time_utils.py       # MJD/UTC conversions
│
├── assets/
│   └── styles.css              # Dark theme custom styles
│
└── tests/
    ├── test_fetchers.py
    └── test_visualizations.py
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Navigate to the project directory:**
   ```bash
   cd astro-dashboard
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard:**
   ```bash
   python app.py
   ```

4. **Open your browser:**
   Navigate to `http://127.0.0.1:8050`

## 📖 Usage Guide

### Monitoring Dashboard

The top section provides real-time monitoring:

1. **Observing Conditions Card**: Shows overall go/no-go status
   - 🟢 Green = Good to observe
   - 🟡 Yellow = Caution advised
   - 🔴 Red = Not recommended

2. **Alert Summary**: Statistics on recent transient alerts
   - Total count by type (GRB, SN, Asteroid, etc.)
   - Average magnitude and age
   - Brightest and newest events

3. **Weather Panel**: Environmental conditions
   - Seeing (arcseconds) with quality indicator
   - Humidity percentage (alert >85%)
   - Wind speed (alert >40 km/h)
   - Temperature and cloud cover

4. **Instrument Panel**: Telescope and detector status
   - CCD temperature and shutter state
   - Guide camera lock status
   - Spectrograph configuration
   - Mount tracking performance

5. **Alert Visualizations**:
   - Sky map showing alert positions (RA/Dec)
   - Pie chart of alert type distribution
   - Magnitude histogram
   - Alert rate time series

### Data Triage Dashboard

The lower section enables interactive data exploration:

1. **Catalog Loading**: Click "Refresh Catalog" to load astronomical catalog data

2. **Linked Brushing**: 
   - Click and drag on any plot to select objects
   - Selections are highlighted across all views:
     - Sky Distribution (RA vs Dec)
     - Magnitude vs Redshift
     - FWHM vs Ellipticity (quality diagram)

3. **Selection Statistics**: View properties of selected objects
   - Coordinate ranges
   - Average magnitude and redshift
   - Object class distribution

4. **Export**: Click "Export Selected" to download target list as CSV

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Observatory location
OBSERVATORY_LAT = -22.9068  # degrees
OBSERVATORY_LON = -43.2356  # degrees

# Operational thresholds
SEEING_GOOD_THRESHOLD = 1.5  # arcseconds
HUMIDITY_ALERT_THRESHOLD = 85  # percent

# Polling intervals (seconds)
VOEVENT_POLL_INTERVAL = 60
WEATHER_POLL_INTERVAL = 30
INSTRUMENT_POLL_INTERVAL = 10

# Mock data toggle
MOCK_WEATHER_DATA = True   # Set False for real sensors
MOCK_INSTRUMENT_DATA = True
```

## 🔧 Development

### Running Tests

```bash
cd astro-dashboard
python -m pytest tests/ -v
```

### Adding New Data Sources

1. Create a new fetcher in `src/data_fetchers/`:
   ```python
   class MyDataFetcher:
       def fetch_data(self):
           # Implementation
           pass
   ```

2. Import and initialize in `app.py`:
   ```python
   from src.data_fetchers.my_fetcher import MyDataFetcher
   my_fetcher = MyDataFetcher()
   ```

3. Add callback for polling:
   ```python
   @app.callback(...)
   def update_my_data(n):
       data = my_fetcher.fetch_data()
       # Update visualizations
   ```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (127.0.0.1:8050)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Dash/Flask Server                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Callbacks │  │   Layout    │  │   dcc.Store State   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  VOEvent Fetch  │ │ Weather Fetch   │ │ FITS Loader     │
│  (astroquery)   │ │ (mock/API)      │ │ (fitsio)        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Alert Parser   │ │ Quality Metrics │ │ Data Aggregator │
│  & Prioritizer  │ │ (FWHM, SNR)     │ │ & Statistics    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Plotly Visualizations                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Sky Maps   │  │ Linked Views│  │  Status Panels      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Offline Operation

The dashboard runs 100% offline with mock data:

- **Mock Alerts**: Simulated VOEvents with realistic distributions
- **Mock Weather**: Generated environmental readings
- **Mock Instruments**: Simulated telescope/detector states
- **Mock Catalog**: 500K object synthetic catalog

To use real data:

1. Set `MOCK_* = False` in `config.py`
2. Configure API endpoints in fetchers
3. Point `MOCK_FITS_PATH` to actual FITS files

## 📝 Logging

Logs are written to stdout with configurable levels:

```python
# In config.py
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

View logs in the terminal where the server is running.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- [Plotly Dash](https://plotly.com/dash/)
- [Astropy](https://www.astropy.org/)
- [fitsio](https://github.com/esheldon/fitsio)
- [astroquery](https://astroquery.readthedocs.io/)

---

**Support**: For issues and questions, please open a GitHub issue.

**Version**: 1.0.0 | **Last Updated**: 2024
