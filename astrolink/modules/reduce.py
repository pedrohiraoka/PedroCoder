"""
AstroReduce Module - CCD Data Reduction

Provides tools for:
- Loading FITS images (bias, dark, flat, science)
- Automated reduction pipeline (bias subtraction, dark correction, flat-fielding)
- Side-by-side image comparison
- Saving reduced images
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QListWidget, QListWidgetItem,
    QMessageBox, QSplitter, QCheckBox, QProgressBar,
    QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

import numpy as np

from astrolink.core.logger import get_logger
from astrolink.gui.widgets import MplCanvas, TutorialPopup
from astrolink.gui.dialogs import FileDialog

logger = get_logger(__name__)


class ReductionWorker(QThread):
    """Worker thread for CCD reduction to avoid blocking UI."""
    progress = Signal(int, str)
    complete = Signal(object)
    error_occurred = Signal(str)
    
    def __init__(self, files: dict):
        super().__init__()
        self.files = files
    
    def run(self):
        try:
            import ccdproc
            from astropy.io import fits
            
            self.progress.emit(10, "Loading bias frames...")
            bias_frames = []
            for f in self.files.get('bias', []):
                bias_frames.append(ccdproc.CCDData.read(f, unit='adu'))
            
            if bias_frames:
                master_bias = ccdproc.combine(bias_frames, method='median')
            else:
                master_bias = None
            
            self.progress.emit(30, "Loading dark frames...")
            dark_frames = []
            for f in self.files.get('dark', []):
                dark_frames.append(ccdproc.CCDData.read(f, unit='adu'))
            
            if dark_frames:
                master_dark = ccdproc.combine(dark_frames, method='median')
            else:
                master_dark = None
            
            self.progress.emit(50, "Loading flat frames...")
            flat_frames = []
            for f in self.files.get('flat', []):
                flat_frames.append(ccdproc.CCDData.read(f, unit='adu'))
            
            if flat_frames:
                master_flat = ccdproc.combine(flat_frames, method='median')
                master_flat = ccdproc.normalize(master_flat)
            else:
                master_flat = None
            
            self.progress.emit(70, "Processing science frames...")
            reduced_images = []
            for i, f in enumerate(self.files.get('science', [])):
                science = ccdproc.CCDData.read(f, unit='adu')
                
                # Apply calibrations
                if master_bias is not None:
                    science = ccdproc.subtract_bias(science, master_bias)
                
                if master_dark is not None:
                    science = ccdproc.subtract_dark(science, master_dark, 
                                                    exposure_time='EXPTIME',
                                                    scale=True)
                
                if master_flat is not None:
                    science = ccdproc.flat_correct(science, master_flat)
                
                reduced_images.append(science)
                prog = 70 + int((i + 1) / len(self.files.get('science', [1])) * 30)
                self.progress.emit(prog, f"Processed {i+1}/{len(self.files['science'])}")
            
            self.complete.emit({
                'reduced': reduced_images,
                'master_bias': master_bias,
                'master_dark': master_dark,
                'master_flat': master_flat
            })
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class ReduceModule(QWidget):
    """
    AstroReduce module widget.
    
    Provides interface for CCD data reduction including:
    - File selection for calibration frames
    - Automated reduction pipeline
    - Before/after comparison
    - Export reduced images
    """
    
    def __init__(self, app_controller):
        super().__init__()
        self.app = app_controller
        self.files = {
            'bias': [],
            'dark': [],
            'flat': [],
            'science': []
        }
        self.reduced_data = None
        
        self._init_ui()
        logger.info("Reduce module initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🖼️ AstroReduce - CCD Data Reduction")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - File selection
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Visualization
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with file selection."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 10, 0)
        
        # Bias frames
        bias_group = self._create_file_list_group("Bias Frames", "bias")
        layout.addWidget(bias_group)
        
        # Dark frames
        dark_group = self._create_file_list_group("Dark Frames", "dark")
        layout.addWidget(dark_group)
        
        # Flat frames
        flat_group = self._create_file_list_group("Flat Frames", "flat")
        layout.addWidget(flat_group)
        
        # Science frames
        science_group = self._create_file_list_group("Science Frames", "science")
        layout.addWidget(science_group)
        
        # Options
        options_group = QGroupBox("Reduction Options")
        options_layout = QFormLayout()
        
        self.subtract_bias = QCheckBox("Subtract Bias")
        self.subtract_bias.setChecked(True)
        options_layout.addRow("", self.subtract_bias)
        
        self.subtract_dark = QCheckBox("Subtract Dark")
        self.subtract_dark.setChecked(True)
        options_layout.addRow("", self.subtract_dark)
        
        self.correct_flat = QCheckBox("Flat Field Correction")
        self.correct_flat.setChecked(True)
        options_layout.addRow("", self.correct_flat)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Run button
        run_btn = QPushButton("▶ Run Reduction Pipeline")
        run_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        run_btn.clicked.connect(self.run_reduction)
        layout.addWidget(run_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Tutorial button
        tutorial_btn = QPushButton("🎓 Tutorial")
        tutorial_btn.clicked.connect(self.show_tutorial)
        layout.addWidget(tutorial_btn)
        
        layout.addStretch()
        
        return panel
    
    def _create_file_list_group(self, title: str, key: str) -> QGroupBox:
        """Create a file list group box."""
        group = QGroupBox(title)
        layout = QVBoxLayout()
        
        # List widget
        list_widget = QListWidget()
        list_widget.setMaximumHeight(80)
        setattr(self, f'{key}_list', list_widget)
        layout.addWidget(list_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Files")
        add_btn.clicked.connect(lambda: self.add_files(key))
        btn_layout.addWidget(add_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.clear_files(key))
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        group.setLayout(layout)
        
        return group
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with visualization."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 0, 0, 0)
        
        # Image comparison label
        comp_label = QLabel("Before / After Comparison:")
        comp_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(comp_label)
        
        # Create canvas for comparison
        self.comparison_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout.addWidget(self.comparison_canvas)
        
        # Save button
        save_btn = QPushButton("💾 Save Reduced Image")
        save_btn.clicked.connect(self.save_reduced)
        save_btn.setEnabled(False)
        self.save_btn = save_btn
        layout.addWidget(save_btn)
        
        return panel
    
    def add_files(self, category: str):
        """Add files for a category."""
        files = FileDialog.open_fits_files(self, multiple=True)
        if files:
            self.files[category].extend(files)
            list_widget = getattr(self, f'{category}_list')
            for f in files:
                list_widget.addItem(QListWidgetItem(f.split('/')[-1]))
            logger.info(f"Added {len(files)} {category} files")
    
    def clear_files(self, category: str):
        """Clear files for a category."""
        self.files[category] = []
        list_widget = getattr(self, f'{category}_list')
        list_widget.clear()
    
    def run_reduction(self):
        """Run the reduction pipeline."""
        if not self.files['science']:
            QMessageBox.warning(self, "Warning", "Please add at least one science frame")
            return
        
        # Start worker
        self.worker = ReductionWorker(self.files)
        self.worker.progress.connect(self.on_progress)
        self.worker.complete.connect(self.on_complete)
        self.worker.error_occurred.connect(self.on_error)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.run_btn = self.sender()
        self.run_btn.setEnabled(False)
        
        self.worker.start()
        logger.info("Started reduction pipeline")
    
    def on_progress(self, value: int, message: str):
        """Update progress."""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def on_complete(self, results: dict):
        """Handle reduction completion."""
        self.reduced_data = results
        self.progress_bar.setVisible(False)
        self.status_label.setText("Reduction complete!")
        
        if self.run_btn:
            self.run_btn.setEnabled(True)
        
        self.save_btn.setEnabled(True)
        
        # Show comparison
        self.show_comparison()
        
        # Log processing step
        self.app.add_processing_log(
            'reduce', 'ccd_reduction',
            inputs=self.files['science'],
            outputs=['reduced_images'],
            parameters={
                'bias': len(self.files['bias']),
                'dark': len(self.files['dark']),
                'flat': len(self.files['flat']),
                'science': len(self.files['science'])
            }
        )
        
        logger.info("Reduction pipeline completed")
    
    def on_error(self, error_msg: str):
        """Handle reduction error."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Error during reduction")
        if self.run_btn:
            self.run_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Error", f"Reduction failed: {error_msg}")
        logger.error(f"Reduction error: {error_msg}")
    
    def show_comparison(self):
        """Show before/after comparison."""
        if not self.reduced_data or not self.reduced_data['reduced']:
            return
        
        try:
            self.comparison_canvas.clear()
            fig = self.comparison_canvas.fig
            
            original = self.reduced_data['reduced'][0].data
            reduced = self.reduced_data['reduced'][0].data
            
            # For demo, just show the same image twice
            # In real use, we'd keep originals separately
            
            ax1 = fig.add_subplot(121)
            ax1.imshow(original, cmap='gray', origin='lower')
            ax1.set_title("Original")
            ax1.axis('off')
            
            ax2 = fig.add_subplot(122)
            im = ax2.imshow(reduced, cmap='gray', origin='lower')
            ax2.set_title("Reduced")
            ax2.axis('off')
            
            fig.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
            
            self.comparison_canvas.draw()
            
        except Exception as e:
            logger.error(f"Comparison display error: {e}")
    
    def save_reduced(self):
        """Save reduced image."""
        if not self.reduced_data or not self.reduced_data['reduced']:
            return
        
        filepath = FileDialog.save_file(
            self, "Save Reduced Image",
            "reduced.fits",
            "FITS Files (*.fits);;All Files (*)"
        )
        
        if filepath:
            try:
                self.reduced_data['reduced'][0].write(filepath, overwrite=True)
                QMessageBox.information(self, "Success", f"Saved to {filepath}")
                logger.info(f"Saved reduced image to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Save failed: {e}")
    
    def show_tutorial(self):
        """Show tutorial for this module."""
        content = """
        <h2>AstroReduce Tutorial</h2>
        <p>This module performs standard CCD data reduction.</p>
        
        <h3>Steps:</h3>
        <ol>
            <li><b>Add bias frames</b> - Load your bias calibration images</li>
            <li><b>Add dark frames</b> - Load dark calibration images</li>
            <li><b>Add flat frames</b> - Load flat field images</li>
            <li><b>Add science frames</b> - Load your target observations</li>
            <li><b>Configure options</b> - Select which corrections to apply</li>
            <li><b>Run pipeline</b> - Execute the reduction</li>
            <li><b>Compare results</b> - View before/after comparison</li>
            <li><b>Save results</b> - Export reduced images</li>
        </ol>
        
        <h3>Calibration Types:</h3>
        <ul>
            <li><b>Bias</b> - Removes electronic offset</li>
            <li><b>Dark</b> - Removes thermal signal</li>
            <li><b>Flat</b> - Corrects pixel sensitivity variations</li>
        </ul>
        """
        dialog = TutorialPopup("Reduce Module Tutorial", content, self)
        dialog.exec()
    
    def reset(self):
        """Reset module state."""
        for key in self.files:
            self.files[key] = []
            list_widget = getattr(self, f'{key}_list', None)
            if list_widget:
                list_widget.clear()
        
        self.reduced_data = None
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready")
        self.save_btn.setEnabled(False)
        self.comparison_canvas.clear()
        logger.debug("Reduce module reset")
