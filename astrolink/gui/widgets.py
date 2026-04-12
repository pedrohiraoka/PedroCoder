"""
Custom widgets for AstroLink GUI.

Includes matplotlib canvas integration, tutorial popups, and other reusable widgets.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QDialog, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    """
    Matplotlib canvas widget for embedding plots in the GUI.
    
    Provides a matplotlib figure embedded in a Qt widget,
    suitable for displaying scientific visualizations.
    """
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """
        Initialize the matplotlib canvas.
        
        Args:
            parent: Parent widget
            width: Figure width in inches
            height: Figure height in inches
            dpi: Figure resolution
        """
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        super().__init__(self.fig)
        
        self.setParent(parent)
        
        # Make canvas expandable
        super().setSizePolicy(
            QWidgetSizePolicy.Expanding,
            QWidgetSizePolicy.Expanding
        )
        super().updateGeometry()
    
    def clear(self):
        """Clear the figure and axes."""
        self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        self.draw()
    
    def save_figure(self, filepath: str, dpi=300):
        """
        Save the figure to a file.
        
        Args:
            filepath: Output file path
            dpi: Resolution for saved figure
        """
        self.fig.savefig(filepath, dpi=dpi, bbox_inches='tight')


# Import QWidgetSizePolicy after PySide6 is available
from PySide6.QtWidgets import QSizePolicy as QWidgetSizePolicy


class TutorialPopup(QDialog):
    """
    Tutorial popup dialog for providing contextual help.
    
    Displays explanations of concepts and step-by-step guides
    based on "Python for Astronomers" content.
    """
    
    def __init__(self, title: str, content: str, parent=None):
        """
        Initialize tutorial popup.
        
        Args:
            title: Dialog title
            content: HTML-formatted content
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(False)
        self.setMinimumSize(500, 400)
        
        # Layout
        layout = QVBoxLayout()
        
        # Content text edit
        self.text_edit = QTextEdit()
        self.text_edit.setHtml(content)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class InfoLabel(QLabel):
    """
    Label widget for displaying informational messages with styling.
    """
    
    def __init__(self, text: str = "", info_type: str = "info", parent=None):
        """
        Initialize info label.
        
        Args:
            text: Label text
            info_type: Type of message ('info', 'warning', 'error', 'success')
            parent: Parent widget
        """
        super().__init__(text, parent)
        
        # Set style based on type
        styles = {
            'info': 'color: #2196F3; font-weight: bold;',
            'warning': 'color: #FF9800; font-weight: bold;',
            'error': 'color: #F44336; font-weight: bold;',
            'success': 'color: #4CAF50; font-weight: bold;'
        }
        
        self.setStyleSheet(styles.get(info_type, styles['info']))
        self.setWordWrap(True)


class ProcessingStatusWidget(QWidget):
    """
    Widget for displaying processing status and progress.
    """
    
    def __init__(self, parent=None):
        """Initialize status widget."""
        super().__init__(parent)
        
        from PySide6.QtWidgets import QVBoxLayout, QLabel, QProgressBar
        
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def set_status(self, message: str):
        """Set status message."""
        self.status_label.setText(message)
    
    def set_progress(self, value: int, total: int = None):
        """
        Set progress value.
        
        Args:
            value: Current progress value
            total: Total value (if None, shows indeterminate progress)
        """
        if total is not None:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(value)
            self.progress_bar.setVisible(True)
        else:
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.progress_bar.setVisible(True)
    
    def hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.setVisible(False)
