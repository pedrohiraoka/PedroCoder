"""
Main application controller for AstroLink.

Manages the application lifecycle, module navigation, and coordination
between different components of the application.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont

from astrolink.core.logger import get_logger, setup_file_logging
from astrolink.core.project import Project
from astrolink.gui.main_window import MainWindow


logger = get_logger(__name__)


class ApplicationSignals(QObject):
    """Signals for application-wide events."""
    project_loaded = Signal(object)  # Emits Project instance
    project_saved = Signal(str)      # Emits file path
    module_changed = Signal(str)     # Emits module name
    data_updated = Signal(object)    # Emits data dictionary


class Application:
    """
    Main application controller for AstroLink.
    
    Manages:
    - Application initialization and lifecycle
    - Project creation/loading/saving
    - Module navigation and coordination
    - Cross-module data flow
    """
    
    def __init__(self):
        """Initialize the AstroLink application."""
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.project: Optional[Project] = None
        self.signals = ApplicationSignals()
        self.current_module: str = "observe"
        
        # Module instances
        self.modules: Dict[str, Any] = {}
        
        logger.info("Initializing AstroLink application")
    
    def initialize(self):
        """
        Initialize the Qt application and main window.
        
        Returns:
            Exit code from app.exec()
        """
        # Setup logging
        if '--debug' in sys.argv:
            setup_file_logging()
        
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("AstroLink")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("AstroLink")
        
        # Set application font
        font = QFont("Segoe UI", 10)
        self.app.setFont(font)
        
        # Create new project by default
        self.new_project("Untitled Project")
        
        # Create and show main window
        self.main_window = MainWindow(self)
        self.main_window.show()
        
        logger.info("AstroLink application started successfully")
        
        return self.app.exec()
    
    def new_project(self, name: str = "Untitled Project"):
        """
        Create a new project.
        
        Args:
            name: Project name
        """
        self.project = Project(name)
        self.signals.project_loaded.emit(self.project)
        logger.info(f"Created new project: {name}")
        
        # Reset modules
        self.modules = {}
    
    def load_project(self, filepath: str):
        """
        Load a project from file.
        
        Args:
            filepath: Path to .astrolink file
        """
        try:
            self.project = Project.load(filepath)
            self.signals.project_loaded.emit(self.project)
            logger.info(f"Loaded project: {filepath}")
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            raise
    
    def save_project(self, filepath: str, include_data: bool = True):
        """
        Save the current project to file.
        
        Args:
            filepath: Path to save .astrolink file
            include_data: Whether to include binary data
        """
        if self.project is None:
            logger.error("No project to save")
            return
        
        try:
            self.project.save(filepath, include_data=include_data)
            self.signals.project_saved.emit(filepath)
            logger.info(f"Saved project: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            raise
    
    def switch_module(self, module_name: str):
        """
        Switch to a different module.
        
        Args:
            module_name: Name of the module to switch to
        """
        if module_name != self.current_module:
            self.current_module = module_name
            self.signals.module_changed.emit(module_name)
            logger.debug(f"Switched to module: {module_name}")
            
            if self.main_window:
                self.main_window.switch_module(module_name)
    
    def register_module(self, name: str, module_instance: Any):
        """
        Register a module with the application.
        
        Args:
            name: Module name
            module_instance: Module instance
        """
        self.modules[name] = module_instance
        logger.debug(f"Registered module: {name}")
    
    def get_module(self, name: str) -> Optional[Any]:
        """
        Get a registered module instance.
        
        Args:
            name: Module name
            
        Returns:
            Module instance or None
        """
        return self.modules.get(name)
    
    def share_data(self, source_module: str, data: Dict[str, Any]):
        """
        Share data between modules.
        
        Args:
            source_module: Source module name
            data: Data to share
        """
        if self.project:
            # Store in project state
            current_state = self.project.get_module_state(source_module)
            current_state.update(data)
            self.project.set_module_state(source_module, current_state)
            
            # Notify other modules
            self.signals.data_updated.emit(data)
            logger.debug(f"Shared data from {source_module}: {list(data.keys())}")
    
    def get_shared_data(self, target_module: str) -> Dict[str, Any]:
        """
        Retrieve shared data for a module.
        
        Args:
            target_module: Target module name
            
        Returns:
            Dictionary of shared data
        """
        if not self.project:
            return {}
        
        all_data = {}
        for module_name, state in self.project.modules_state.items():
            if module_name != target_module:
                all_data[module_name] = state
        
        return all_data
    
    def add_processing_log(self, module: str, action: str, **kwargs):
        """
        Add an entry to the processing log.
        
        Args:
            module: Module name
            action: Action performed
            **kwargs: Additional parameters
        """
        if self.project:
            self.project.add_processing_step(module, action, **kwargs)
    
    def quit(self):
        """Quit the application."""
        if self.app:
            logger.info("Quitting AstroLink application")
            self.app.quit()


def run():
    """
    Entry point for running AstroLink.
    
    Returns:
        Exit code from application
    """
    app = Application()
    return app.initialize()
