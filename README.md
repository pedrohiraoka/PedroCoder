# 🌌 AstroLink - Your Intelligent Astronomical Laboratory

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-MVP-brightgreen.svg)]()

**AstroLink** is a revolutionary, integrated desktop application that unifies all stages of the astronomical workflow into a single, intuitive graphical interface. Built with Python and powered by established scientific libraries, AstroLink acts as a "smart laboratory notebook" for astronomers, students, researchers, and enthusiasts.

## ✨ Features

### Core Modules (MVP v1.0)

#### 🔭 **AstroObserve** - Observation Planning
- Search astronomical catalogs (Simbad, Vizier) via `astroquery`
- Calculate target visibility and ephemerides using `astroplan`
- Generate interactive celestial charts with `aplpy`
- Export target lists and ephemerides to CSV/TeX formats
- Support for custom telescope locations and presets

#### 🖼️ **AstroReduce** - CCD Data Reduction
- Load bias, dark, flat, and science FITS images
- Automated reduction pipeline (bias subtraction, dark correction, flat-fielding) via `ccdproc`
- Side-by-side comparison of raw and reduced images
- Manual calibration options and distortion correction
- Native FITS support through `astropy.io.fits`

#### 📊 **AstroAnalyze** - Photometry & Spectroscopy
- Source detection and aperture photometry with `photutils`
- PSF fitting and region-of-interest selection
- Light curve generation and analysis
- Spectral analysis with `specutils` and `pyspeckit`
- Interactive plots with `matplotlib` and `plotly`

#### 🧮 **AstroModel** - Bayesian Modeling & Simulations
- Curve fitting with user-defined models using `lmfit`
- Bayesian inference with `emcee` and `dynesty`
- N-body simulations with `rebound`
- Visualization of posterior distributions and simulated orbits

#### 📝 **AstroPublish** - Scientific Export
- Generate publication-ready figures (high-resolution PNG/PDF)
- Export tables to LaTeX, CSV, and FITS formats
- Automatic processing logs for pipeline traceability
- Optional Git/GitHub integration for version control

### Additional Features

- **🎓 Tutorial Mode**: Step-by-step guides based on "Python for Astronomers"
- **💾 AstroSnap**: Save and restore project state (data, parameters, results)
- **🤖 AstroChat**: Local AI assistant for technical questions (powered by llama.cpp)
- **👥 Collaborative Mode**: Export/import projects in `.astrolink` format

## 🛠️ Technology Stack

| Category | Libraries |
|----------|-----------|
| **GUI Framework** | PySide6 |
| **Astronomy Core** | astropy, astroplan, astroquery, ccdproc |
| **Analysis** | photutils, specutils, pyspeckit, aplpy |
| **Modeling** | lmfit, emcee, dynesty, rebound |
| **Visualization** | matplotlib, seaborn, plotly |
| **Data Processing** | numpy, scipy, pandas, dask |
| **Storage** | h5py, sqlalchemy, tabulate |

### Why PySide6?

We chose **PySide6** over DearPyGui for the following reasons:

1. **Matplotlib Integration**: PySide6 provides seamless embedding of matplotlib canvases via `FigureCanvasQTAgg`, crucial for scientific visualization
2. **Mature Ecosystem**: Qt has decades of development with extensive documentation and community support
3. **Cross-Platform Stability**: Proven track record on Windows, macOS, and Linux
4. **Rich Widget Set**: Comprehensive collection of native widgets for complex UIs
5. **Professional Look**: Native look-and-feel across all platforms

## 📋 Requirements

- Python >= 3.9
- Operating System: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- 4GB RAM minimum (8GB recommended for large datasets)
- 2GB free disk space

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/astrolink.git
cd astrolink
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run AstroLink

```bash
python main.py
```

## 📖 Usage Guide

### Quick Start Tutorial

1. **Launch AstroLink**: Run `python main.py` from the command line
2. **Create New Project**: Click "File → New Project" to start a fresh session
3. **Plan Observations** (AstroObserve):
   - Enter target coordinates or search Simbad
   - Set your observatory location
   - Generate visibility charts and export ephemerides
4. **Reduce Data** (AstroReduce):
   - Load your FITS files (bias, dark, flat, science)
   - Run the automated reduction pipeline
   - Compare before/after images
5. **Analyze Results** (AstroAnalyze):
   - Perform aperture photometry on reduced images
   - Generate light curves
   - Export data for further analysis
6. **Model Phenomena** (AstroModel):
   - Fit models to your data
   - Run Bayesian inference
   - Visualize results
7. **Publish** (AstroPublish):
   - Generate publication-quality figures
   - Export tables to LaTeX
   - Save complete processing logs

### Project Files (.astrolink)

AstroLink uses a custom `.astrolink` format to save project state:

```python
# Save current project
File → Save Project As... → myproject.astrolink

# Load existing project
File → Open Project... → myproject.astrolink
```

The `.astrolink` file contains:
- All input file paths
- Processing parameters
- Intermediate results
- Generated plots and tables
- Complete processing history

## 📁 Project Structure

```
astrolink/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── astrolink/
│   ├── __init__.py        # Package initialization
│   ├── core/
│   │   ├── __init__.py
│   │   ├── app.py         # Main application controller
│   │   ├── project.py     # Project state management
│   │   └── logger.py      # Logging utilities
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── observe.py     # AstroObserve module
│   │   ├── reduce.py      # AstroReduce module
│   │   ├── analyze.py     # AstroAnalyze module
│   │   ├── model.py       # AstroModel module
│   │   └── publish.py     # AstroPublish module
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py # Main application window
│   │   ├── widgets.py     # Custom widgets
│   │   └── dialogs.py     # Dialog windows
│   └── utils/
│       ├── __init__.py
│       ├── fits_utils.py  # FITS file utilities
│       └── export.py      # Export functions
└── data/
    └── sample/            # Sample FITS files for testing
```

## 🧪 Testing with Sample Data

AstroLink includes sample FITS files for testing each module:

```bash
# Located in astrolink/data/sample/
- bias.fits
- dark.fits
- flat.fits
- science.fits
- spectrum.fits
```

Load these files to explore AstroLink's features without your own data.

## 🔧 Configuration

AstroLink can be configured via environment variables:

```bash
# Set custom data directory
export ASTROLINK_DATA_DIR=/path/to/data

# Enable debug logging
export ASTROLINK_DEBUG=1

# Set log level (DEBUG, INFO, WARNING, ERROR)
export ASTROLINK_LOG_LEVEL=DEBUG
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest

# Format code
black astrolink/

# Lint code
flake8 astrolink/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the book "Python for Astronomers"
- Built upon the incredible work of the Astropy project
- Thanks to all contributors of the scientific Python ecosystem

## 📞 Support

- **Documentation**: [Wiki](https://github.com/yourusername/astrolink/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/astrolink/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/astrolink/discussions)
- **Email**: support@astrolink.example.com

## 🗺️ Roadmap

### Post-MVP Features (v2.0+)
- [ ] Integration with robotic telescope APIs
- [ ] Machine learning module for object classification
- [ ] Web interface (Streamlit/Dash)
- [ ] VS Code and Jupyter plugins
- [ ] 2D spectroscopy support
- [ ] Real-time collaboration features
- [ ] Cloud storage integration

---

**Made with ❤️ for the Astronomy Community**

*AstroLink - Bridging the gap between powerful Python libraries and intuitive astronomical workflows.*
