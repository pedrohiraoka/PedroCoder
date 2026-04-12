"""
AstroPublish Module - Scientific Export

Provides tools for:
- Generating publication-ready figures
- Exporting tables to LaTeX and CSV
- Processing log export
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QMessageBox, QListWidget,
    QListWidgetItem, QSpinBox, QComboBox
)
from PySide6.QtGui import QFont

from astrolink.core.logger import get_logger
from astrolink.gui.widgets import MplCanvas, TutorialPopup
from astrolink.gui.dialogs import FileDialog

logger = get_logger(__name__)


class PublishModule(QWidget):
    """
    AstroPublish module widget.
    
    Provides interface for scientific publishing and export.
    """
    
    def __init__(self, app_controller):
        super().__init__()
        self.app = app_controller
        
        self._init_ui()
        logger.info("Publish module initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📝 AstroPublish - Scientific Export")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Figure export group
        fig_group = self._create_figure_export_group()
        layout.addWidget(fig_group)
        
        # Table export group
        table_group = self._create_table_export_group()
        layout.addWidget(table_group)
        
        # Log export
        log_group = self._create_log_export_group()
        layout.addWidget(log_group)
        
        # Tutorial button
        tutorial_btn = QPushButton("🎓 Tutorial")
        tutorial_btn.clicked.connect(self.show_tutorial)
        layout.addWidget(tutorial_btn)
        
        self.setLayout(layout)
    
    def _create_figure_export_group(self) -> QGroupBox:
        """Create figure export controls."""
        group = QGroupBox("Figure Export")
        layout = QFormLayout()
        
        # Resolution selection
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        self.dpi_spin.setSuffix(" DPI")
        layout.addRow("Resolution:", self.dpi_spin)
        
        # Format selection
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "PDF", "SVG", "EPS"])
        layout.addRow("Format:", self.format_combo)
        
        # Export button
        export_fig_btn = QPushButton("Export Current Figure")
        export_fig_btn.clicked.connect(self.export_figure)
        layout.addRow("", export_fig_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_table_export_group(self) -> QGroupBox:
        """Create table export controls."""
        group = QGroupBox("Table Export")
        layout = QVBoxLayout()
        
        info_label = QLabel("Available data sources:")
        layout.addWidget(info_label)
        
        self.data_list = QListWidget()
        self.data_list.setMaximumHeight(100)
        self.data_list.addItem("Photometry Results")
        self.data_list.addItem("Observation Targets")
        self.data_list.addItem("Fit Parameters")
        layout.addWidget(self.data_list)
        
        # Format buttons
        btn_layout = QHBoxLayout()
        
        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(lambda: self.export_table('csv'))
        btn_layout.addWidget(csv_btn)
        
        latex_btn = QPushButton("Export LaTeX")
        latex_btn.clicked.connect(lambda: self.export_table('latex'))
        btn_layout.addWidget(latex_btn)
        
        layout.addLayout(btn_layout)
        group.setLayout(layout)
        return group
    
    def _create_log_export_group(self) -> QGroupBox:
        """Create log export controls."""
        group = QGroupBox("Processing Log")
        layout = QVBoxLayout()
        
        log_info = QLabel(f"Processing steps recorded: {len(self.app.project.processing_history) if self.app.project else 0}")
        layout.addWidget(log_info)
        
        export_log_btn = QPushButton("Export Processing Log")
        export_log_btn.clicked.connect(self.export_log)
        layout.addWidget(export_log_btn)
        
        group.setLayout(layout)
        return group
    
    def export_figure(self):
        """Export a figure with publication settings."""
        try:
            # Get current module's canvas (for demo, just create a sample plot)
            import matplotlib.pyplot as plt
            
            dpi = self.dpi_spin.value()
            fmt = self.format_combo.currentText().lower()
            
            filepath = FileDialog.save_file(
                self, "Export Figure",
                f"figure.{fmt}",
                f"{fmt.upper()} Files (*.{fmt});;All Files (*)"
            )
            
            if filepath:
                # Create a sample publication-quality figure
                fig, ax = plt.subplots(figsize=(8, 6), dpi=dpi)
                
                # Sample data
                import numpy as np
                x = np.linspace(0, 10, 100)
                y = np.exp(-x/5) * np.sin(x)
                
                ax.plot(x, y, 'b-', linewidth=2, label='Data')
                ax.set_xlabel('X axis (units)', fontsize=12)
                ax.set_ylabel('Y axis (units)', fontsize=12)
                ax.set_title('Sample Publication Figure', fontsize=14)
                ax.legend(fontsize=10)
                ax.grid(True, alpha=0.3)
                
                # Save with high quality settings
                fig.savefig(filepath, dpi=dpi, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # Log processing
                self.app.add_processing_log(
                    'publish', 'export_figure',
                    outputs=[filepath],
                    parameters={
                        'dpi': dpi,
                        'format': fmt
                    }
                )
                
                QMessageBox.information(self, "Success", f"Exported to {filepath}")
                logger.info(f"Exported figure to {filepath}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")
            logger.error(f"Figure export error: {e}")
    
    def export_table(self, format: str):
        """Export table data."""
        if not self.app.project:
            QMessageBox.warning(self, "Warning", "No project loaded")
            return
        
        selected = self.data_list.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Warning", "Please select a data source")
            return
        
        data_sources = ["photometry", "targets", "fit_params"]
        source = data_sources[selected] if selected < len(data_sources) else "data"
        
        ext = 'tex' if format == 'latex' else 'csv'
        filepath = FileDialog.save_file(
            self, f"Export {format.upper()}",
            f"{source}.{ext}",
            f"{format.upper()} Files (*.{ext});;All Files (*)"
        )
        
        if filepath:
            try:
                if format == 'latex':
                    # Create sample LaTeX table
                    content = """\\begin{table}[h]
\\centering
\\caption{Sample Data Table}
\\begin{tabular}{ccc}
\\hline
Column1 & Column2 & Column3 \\\\
\\hline
1.0 & 2.0 & 3.0 \\\\
4.0 & 5.0 & 6.0 \\\\
7.0 & 8.0 & 9.0 \\\\
\\hline
\\end{tabular}
\\end{table}
"""
                    with open(filepath, 'w') as f:
                        f.write(content)
                else:
                    # Create sample CSV
                    import csv
                    with open(filepath, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Column1', 'Column2', 'Column3'])
                        writer.writerow([1.0, 2.0, 3.0])
                        writer.writerow([4.0, 5.0, 6.0])
                
                # Log processing
                self.app.add_processing_log(
                    'publish', f'export_table_{format}',
                    outputs=[filepath],
                    parameters={'source': source}
                )
                
                QMessageBox.information(self, "Success", f"Exported to {filepath}")
                logger.info(f"Exported table to {filepath}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {e}")
                logger.error(f"Table export error: {e}")
    
    def export_log(self):
        """Export the processing log."""
        if not self.app.project:
            QMessageBox.warning(self, "Warning", "No project loaded")
            return
        
        filepath = FileDialog.save_file(
            self, "Export Processing Log",
            "processing_log.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filepath:
            try:
                self.app.project.export_log(filepath)
                QMessageBox.information(self, "Success", f"Log exported to {filepath}")
                logger.info(f"Exported processing log to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {e}")
    
    def show_tutorial(self):
        """Show tutorial for this module."""
        content = """
        <h2>AstroPublish Tutorial</h2>
        <p>This module helps you prepare results for publication.</p>
        
        <h3>Figure Export:</h3>
        <ol>
            <li><b>Select resolution</b> - Choose DPI (300+ for publications)</li>
            <li><b>Choose format</b> - PNG for presentations, PDF/SVG for papers</li>
            <li><b>Export</b> - Save your figure</li>
        </ol>
        
        <h3>Table Export:</h3>
        <ol>
            <li><b>Select data</b> - Choose which dataset to export</li>
            <li><b>Choose format</b> - CSV for data analysis, LaTeX for papers</li>
            <li><b>Export</b> - Save your table</li>
        </ol>
        
        <h3>Tips:</h3>
        <ul>
            <li>Use 300+ DPI for journal submissions</li>
            <li>PDF/SVG formats preserve vector graphics</li>
            <li>LaTeX tables integrate directly with papers</li>
            <li>Processing logs provide reproducibility</li>
        </ul>
        """
        dialog = TutorialPopup("Publish Module Tutorial", content, self)
        dialog.exec()
