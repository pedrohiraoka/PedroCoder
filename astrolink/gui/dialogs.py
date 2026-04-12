"""
Dialog windows for AstroLink GUI.

Includes file dialogs, progress dialogs, and other utility dialogs.
"""

from PySide6.QtWidgets import (
    QFileDialog, QDialog, QVBoxLayout, QLabel, 
    QProgressBar, QPushButton, QHBoxLayout, QApplication
)
from PySide6.QtCore import Qt
from pathlib import Path


class FileDialog:
    """
    Utility class for file selection dialogs.
    
    Provides static methods for common file selection operations
    with appropriate filters for astronomical data files.
    """
    
    @staticmethod
    def open_fits_files(parent=None, multiple=True):
        """
        Open dialog for selecting FITS files.
        
        Args:
            parent: Parent widget
            multiple: Allow multiple file selection
            
        Returns:
            List of selected file paths
        """
        filter_str = "FITS Files (*.fits *.fit *.fts);;All Files (*)"
        
        if multiple:
            files, _ = QFileDialog.getOpenFileNames(
                parent, "Select FITS Files", "", filter_str
            )
        else:
            file, _ = QFileDialog.getOpenFileName(
                parent, "Select FITS File", "", filter_str
            )
            files = [file] if file else []
        
        return files
    
    @staticmethod
    def save_file(parent=None, title="Save File", default_name="", file_type="All Files (*)"):
        """
        Open dialog for saving a file.
        
        Args:
            parent: Parent widget
            title: Dialog title
            default_name: Default filename
            file_type: File type filter
            
        Returns:
            Selected file path or None
        """
        filepath, _ = QFileDialog.getSaveFileName(
            parent, title, default_name, file_type
        )
        return filepath if filepath else None
    
    @staticmethod
    def open_directory(parent=None, caption="Select Directory"):
        """
        Open dialog for selecting a directory.
        
        Args:
            parent: Parent widget
            caption: Dialog caption
            
        Returns:
            Selected directory path or None
        """
        directory = QFileDialog.getExistingDirectory(
            parent, caption, "", QFileDialog.ShowDirsOnly
        )
        return directory if directory else None
    
    @staticmethod
    def open_project_file(parent=None):
        """
        Open dialog for selecting an AstroLink project file.
        
        Args:
            parent: Parent widget
            
        Returns:
            Selected file path or None
        """
        filter_str = "AstroLink Project (*.astrolink);;All Files (*)"
        filepath, _ = QFileDialog.getOpenFileName(
            parent, "Open Project", "", filter_str
        )
        return filepath if filepath else None
    
    @staticmethod
    def save_project_file(parent=None, default_name="project.astrolink"):
        """
        Open dialog for saving an AstroLink project file.
        
        Args:
            parent: Parent widget
            default_name: Default filename
            
        Returns:
            Selected file path or None
        """
        filter_str = "AstroLink Project (*.astrolink);;All Files (*)"
        filepath, _ = QFileDialog.getSaveFileName(
            parent, "Save Project", default_name, filter_str
        )
        return filepath if filepath else None


class ProgressDialog(QDialog):
    """
    Dialog for displaying processing progress.
    
    Shows a progress bar with status message during long-running operations.
    """
    
    def __init__(self, parent=None, title="Processing", max_value=100):
        """
        Initialize progress dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            max_value: Maximum progress value
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Layout
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(max_value)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self._cancelled = False
    
    def set_status(self, message: str):
        """Update status message."""
        self.status_label.setText(message)
        QApplication.processEvents()
    
    def set_progress(self, value: int):
        """Update progress value."""
        self.progress_bar.setValue(value)
        QApplication.processEvents()
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._cancelled
    
    def reject(self):
        """Handle dialog rejection (cancel)."""
        self._cancelled = True
        super().reject()


class MessageDialog(QDialog):
    """
    Simple message dialog for displaying information, warnings, or errors.
    """
    
    def __init__(self, title: str, message: str, msg_type="info", parent=None):
        """
        Initialize message dialog.
        
        Args:
            title: Dialog title
            message: Message text
            msg_type: Message type ('info', 'warning', 'error', 'question')
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Layout
        layout = QVBoxLayout()
        
        # Message label
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Set icon based on type
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'question': '❓'
        }
        self.setWindowTitle(f"{icons.get(msg_type, 'ℹ️')} {title}")
