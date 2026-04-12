"""
AstroAnalyze Module - Photometry & Spectroscopy

Provides tools for:
- Aperture photometry with photutils
- Source detection
- Light curve generation
- Spectral analysis with specutils
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QMessageBox, QSplitter,
    QTabWidget, QDoubleSpinBox, QComboBox
)
from PySide6.QtGui import QFont

from astrolink.core.logger import get_logger
from astrolink.gui.widgets import MplCanvas, TutorialPopup
from astrolink.gui.dialogs import FileDialog

logger = get_logger(__name__)


class AnalyzeModule(QWidget):
    """
    AstroAnalyze module widget.
    
    Provides interface for photometry and spectroscopy analysis.
    """
    
    def __init__(self, app_controller):
        super().__init__()
        self.app = app_controller
        self.image_data = None
        self.photometry_results = None
        
        self._init_ui()
        logger.info("Analyze module initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📊 AstroAnalyze - Photometry & Spectroscopy")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Photometry tab
        photometry_tab = self._create_photometry_tab()
        tabs.addTab(photometry_tab, "Photometry")
        
        # Spectroscopy tab
        spectroscopy_tab = self._create_spectroscopy_tab()
        tabs.addTab(spectroscopy_tab, "Spectroscopy")
        
        layout.addWidget(tabs)
        
        # Tutorial button
        tutorial_btn = QPushButton("🎓 Tutorial")
        tutorial_btn.clicked.connect(self.show_tutorial)
        layout.addWidget(tutorial_btn)
        
        self.setLayout(layout)
    
    def _create_photometry_tab(self) -> QWidget:
        """Create photometry analysis tab."""
        panel = QWidget()
        layout = QHBoxLayout()
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Load image
        load_group = QGroupBox("Image")
        load_layout = QFormLayout()
        
        load_btn = QPushButton("Load FITS Image")
        load_btn.clicked.connect(self.load_image)
        load_layout.addRow("", load_btn)
        
        load_group.setLayout(load_layout)
        left_layout.addWidget(load_group)
        
        # Photometry parameters
        param_group = QGroupBox("Photometry Parameters")
        param_layout = QFormLayout()
        
        self.aperture_radius = QDoubleSpinBox()
        self.aperture_radius.setRange(1, 100)
        self.aperture_radius.setValue(5)
        self.aperture_radius.setSuffix(" pixels")
        param_layout.addRow("Aperture Radius:", self.aperture_radius)
        
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0, 100)
        self.threshold.setValue(3)
        self.threshold.setSuffix(" sigma")
        param_layout.addRow("Detection Threshold:", self.threshold)
        
        run_phot_btn = QPushButton("Run Photometry")
        run_phot_btn.clicked.connect(self.run_photometry)
        param_layout.addRow("", run_phot_btn)
        
        param_group.setLayout(param_layout)
        left_layout.addWidget(param_group)
        
        # Export
        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.export_photometry)
        left_layout.addWidget(export_btn)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # Right panel - Visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        self.image_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        right_layout.addWidget(self.image_canvas)
        
        self.lightcurve_canvas = MplCanvas(self, width=5, height=3, dpi=100)
        right_layout.addWidget(self.lightcurve_canvas)
        
        right_panel.setLayout(right_layout)
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        panel.setLayout(layout)
        
        return panel
    
    def _create_spectroscopy_tab(self) -> QWidget:
        """Create spectroscopy analysis tab."""
        panel = QWidget()
        layout = QVBoxLayout()
        
        info_label = QLabel("Spectroscopy analysis coming soon...")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        self.spectrum_canvas = MplCanvas(self, width=6, height=4, dpi=100)
        layout.addWidget(self.spectrum_canvas)
        
        panel.setLayout(layout)
        return panel
    
    def load_image(self):
        """Load a FITS image for analysis."""
        files = FileDialog.open_fits_files(self, multiple=False)
        if files:
            try:
                from astropy.io import fits
                with fits.open(files[0]) as hdul:
                    self.image_data = hdul[0].data
                
                self.show_image()
                logger.info(f"Loaded image: {files[0]}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
    
    def show_image(self):
        """Display the loaded image."""
        if self.image_data is None:
            return
        
        try:
            self.image_canvas.clear()
            ax = self.image_canvas.axes
            
            im = ax.imshow(self.image_data, cmap='gray', origin='lower')
            ax.set_title("Loaded Image")
            ax.axis('off')
            
            self.image_canvas.fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            self.image_canvas.draw()
        except Exception as e:
            logger.error(f"Image display error: {e}")
    
    def run_photometry(self):
        """Run aperture photometry on the loaded image."""
        if self.image_data is None:
            QMessageBox.warning(self, "Warning", "Please load an image first")
            return
        
        try:
            import numpy as np
            from photutils.detection import DAOStarFinder
            from photutils.aperture import CircularAperture, aperture_photometry
            
            # Detect sources
            daofind = DAOStarFinder(
                threshold=self.threshold.value() * np.std(self.image_data),
                fwhm=3.0
            )
            sources = daofind(self.image_data)
            
            if len(sources) == 0:
                QMessageBox.information(self, "Info", "No sources detected")
                return
            
            # Perform aperture photometry
            positions = list(zip(sources['xcentroid'], sources['ycentroid']))
            apertures = CircularAperture(positions, r=self.aperture_radius.value())
            phot_table = aperture_photometry(self.image_data, apertures)
            
            self.photometry_results = {
                'sources': sources,
                'photometry': phot_table
            }
            
            # Display results on image
            self.show_image()
            ax = self.image_canvas.axes
            ax.plot(sources['xcentroid'], sources['ycentroid'], 'r+', markersize=10)
            self.image_canvas.draw()
            
            # Generate light curve placeholder
            self.show_lightcurve(sources)
            
            # Log processing
            self.app.add_processing_log(
                'analyze', 'photometry',
                outputs=['photometry_results'],
                parameters={
                    'aperture_radius': self.aperture_radius.value(),
                    'threshold': self.threshold.value(),
                    'sources_found': len(sources)
                }
            )
            
            logger.info(f"Found {len(sources)} sources")
            
        except ImportError:
            QMessageBox.warning(self, "Warning", "photutils not available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Photometry failed: {e}")
            logger.error(f"Photometry error: {e}")
    
    def show_lightcurve(self, sources):
        """Display a simple light curve plot."""
        try:
            self.lightcurve_canvas.clear()
            ax = self.lightcurve_canvas.axes
            
            # For demo, just show source brightness distribution
            if 'aperture_sum' in sources.colnames:
                flux = sources['aperture_sum']
                ax.hist(flux, bins=20, edgecolor='black')
                ax.set_xlabel("Flux (ADU)")
                ax.set_ylabel("Number of Sources")
                ax.set_title("Source Flux Distribution")
            else:
                ax.text(0.5, 0.5, "No photometry data", ha='center', va='center')
            
            self.lightcurve_canvas.draw()
        except Exception as e:
            logger.error(f"Lightcurve display error: {e}")
    
    def export_photometry(self):
        """Export photometry results."""
        if not self.photometry_results:
            QMessageBox.warning(self, "Warning", "No photometry results to export")
            return
        
        filepath = FileDialog.save_file(
            self, "Export Photometry",
            "photometry.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filepath:
            try:
                self.photometry_results['photometry'].write(filepath, format='csv', overwrite=True)
                QMessageBox.information(self, "Success", f"Exported to {filepath}")
                logger.info(f"Exported photometry to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {e}")
    
    def show_tutorial(self):
        """Show tutorial for this module."""
        content = """
        <h2>AstroAnalyze Tutorial</h2>
        <p>This module performs photometric and spectroscopic analysis.</p>
        
        <h3>Photometry Steps:</h3>
        <ol>
            <li><b>Load image</b> - Open a FITS image file</li>
            <li><b>Set parameters</b> - Configure aperture radius and detection threshold</li>
            <li><b>Run photometry</b> - Detect sources and measure fluxes</li>
            <li><b>Review results</b> - Check detected sources on image</li>
            <li><b>Export</b> - Save photometry table to CSV</li>
        </ol>
        
        <h3>Tips:</h3>
        <ul>
            <li>Adjust threshold to control sensitivity</li>
            <li>Larger apertures capture more flux but may include background</li>
            <li>Check that sources are properly centered in apertures</li>
        </ul>
        """
        dialog = TutorialPopup("Analyze Module Tutorial", content, self)
        dialog.exec()
    
    def reset(self):
        """Reset module state."""
        self.image_data = None
        self.photometry_results = None
        self.image_canvas.clear()
        self.lightcurve_canvas.clear()
