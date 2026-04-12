"""
Main application window for AstroLink.

Provides the primary user interface with navigation between modules,
menu bar, and status bar.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QMenuBar, QMenu, QAction, QToolBar,
    QLabel, QPushButton, QFrame, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

from astrolink.core.logger import get_logger
from astrolink.gui.dialogs import FileDialog, MessageDialog
from astrolink.gui.widgets import MplCanvas


logger = get_logger(__name__)


class ModuleButton(QPushButton):
    """Styled button for module navigation."""
    
    def __init__(self, name: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.module_name = name
        self.setText(name)
        self.setCheckable(True)
        self.setMinimumHeight(40)
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover:!checked {
                background-color: #e0e0e0;
            }
        """)


class MainWindow(QMainWindow):
    """
    Main application window for AstroLink.
    
    Contains:
    - Menu bar with file, edit, help menus
    - Toolbar with quick actions
    - Module navigation sidebar
    - Stacked widget for module content
    - Status bar
    """
    
    # Signals
    module_changed = Signal(str)
    
    def __init__(self, app_controller):
        """
        Initialize main window.
        
        Args:
            app_controller: Application controller instance
        """
        super().__init__()
        
        self.app = app_controller
        self.current_module = "observe"
        
        # Window setup
        self.setWindowTitle("AstroLink - Your Intelligent Astronomical Laboratory")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create sidebar for module navigation
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Create stacked widget for module content
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: white;")
        main_layout.addWidget(self.stacked_widget)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create toolbar
        self._create_toolbar()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Load module widgets
        self._load_modules()
        
        logger.info("Main window initialized")
    
    def _create_sidebar(self) -> QWidget:
        """Create the left sidebar with module navigation."""
        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-right: 1px solid #ddd;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🔭 AstroLink")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("v1.0.0")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Module buttons
        self.module_buttons = {}
        modules = [
            ("observe", "🔭 Observe"),
            ("reduce", "🖼️ Reduce"),
            ("analyze", "📊 Analyze"),
            ("model", "🧮 Model"),
            ("publish", "📝 Publish")
        ]
        
        for module_id, module_name in modules:
            btn = ModuleButton(module_name)
            btn.clicked.connect(lambda checked, mid=module_id: self.switch_module(mid))
            layout.addWidget(btn)
            self.module_buttons[module_id] = btn
        
        # Set first module as active
        self.module_buttons["observe"].setChecked(True)
        
        layout.addStretch()
        
        # Tutorial button
        tutorial_btn = QPushButton("🎓 Tutorial")
        tutorial_btn.clicked.connect(self.show_tutorial)
        layout.addWidget(tutorial_btn)
        
        return sidebar
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_log_action = QAction("Export &Log...", self)
        export_log_action.triggered.connect(self.export_log)
        file_menu.addAction(export_log_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About AstroLink", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        tutorial_action = QAction("&Tutorial", self)
        tutorial_action.setShortcut("F1")
        tutorial_action.triggered.connect(self.show_tutorial)
        help_menu.addAction(tutorial_action)
    
    def _create_toolbar(self):
        """Create the application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # New project action
        new_action = QAction("📄 New", self)
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)
        
        # Open project action
        open_action = QAction("📂 Open", self)
        open_action.triggered.connect(self.open_project)
        toolbar.addAction(open_action)
        
        # Save project action
        save_action = QAction("💾 Save", self)
        save_action.triggered.connect(self.save_project)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Tutorial action
        tutorial_action = QAction("🎓 Tutorial", self)
        tutorial_action.triggered.connect(self.show_tutorial)
        toolbar.addAction(tutorial_action)
    
    def _load_modules(self):
        """Load all module widgets into the stacked widget."""
        from astrolink.modules.observe import ObserveModule
        from astrolink.modules.reduce import ReduceModule
        from astrolink.modules.analyze import AnalyzeModule
        from astrolink.modules.model import ModelModule
        from astrolink.modules.publish import PublishModule
        
        # Create module instances
        self.modules = {
            "observe": ObserveModule(self.app),
            "reduce": ReduceModule(self.app),
            "analyze": AnalyzeModule(self.app),
            "model": ModelModule(self.app),
            "publish": PublishModule(self.app)
        }
        
        # Add to stacked widget
        for module_widget in self.modules.values():
            self.stacked_widget.addWidget(module_widget)
        
        # Register modules with app
        for name, widget in self.modules.items():
            self.app.register_module(name, widget)
    
    def switch_module(self, module_name: str):
        """
        Switch to a different module.
        
        Args:
            module_name: Name of the module to switch to
        """
        if module_name not in self.modules:
            logger.warning(f"Unknown module: {module_name}")
            return
        
        # Update button states
        for name, btn in self.module_buttons.items():
            btn.setChecked(name == module_name)
        
        # Switch stacked widget
        index = list(self.modules.keys()).index(module_name)
        self.stacked_widget.setCurrentIndex(index)
        
        self.current_module = module_name
        self.module_changed.emit(module_name)
        
        logger.debug(f"Switched to module: {module_name}")
        self.statusBar().showMessage(f"Module: {module_name.capitalize()}")
    
    def new_project(self):
        """Create a new project."""
        reply = QMessageBox.question(
            self, "New Project",
            "Create a new project? Unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.app.new_project("Untitled Project")
            self.statusBar().showMessage("New project created")
            
            # Reset all modules
            for module in self.modules.values():
                if hasattr(module, 'reset'):
                    module.reset()
    
    def open_project(self):
        """Open an existing project."""
        filepath = FileDialog.open_project_file(self)
        if filepath:
            try:
                self.app.load_project(filepath)
                self.statusBar().showMessage(f"Opened: {filepath}")
                
                # Refresh modules
                for module in self.modules.values():
                    if hasattr(module, 'refresh'):
                        module.refresh()
            except Exception as e:
                MessageDialog("Error", f"Failed to open project: {e}", "error", self).exec()
    
    def save_project(self):
        """Save the current project."""
        if self.app.project and self.app.project._current_file:
            self.app.save_project(self.app.project._current_file)
            self.statusBar().showMessage("Project saved")
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Save project with a new filename."""
        filepath = FileDialog.save_project_file(self)
        if filepath:
            self.app.save_project(filepath)
            self.statusBar().showMessage(f"Saved: {filepath}")
    
    def export_log(self):
        """Export processing log."""
        filepath = FileDialog.save_file(
            self, "Export Log", "processing_log.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        if filepath and self.app.project:
            self.app.project.export_log(filepath)
            self.statusBar().showMessage(f"Log exported: {filepath}")
    
    def show_tutorial(self):
        """Show tutorial dialog."""
        from astrolink.gui.widgets import TutorialPopup
        
        content = """
        <h2>Welcome to AstroLink!</h2>
        <p>AstroLink is your integrated astronomical laboratory.</p>
        
        <h3>Getting Started:</h3>
        <ol>
            <li><b>Observe</b> - Plan your observations and search catalogs</li>
            <li><b>Reduce</b> - Process CCD data (bias, dark, flat correction)</li>
            <li><b>Analyze</b> - Perform photometry and spectroscopy</li>
            <li><b>Model</b> - Fit models and run simulations</li>
            <li><b>Publish</b> - Export publication-ready figures and tables</li>
        </ol>
        
        <h3>Tips:</h3>
        <ul>
            <li>Results flow between modules automatically</li>
            <li>Save your project frequently using Ctrl+S</li>
            <li>Use the Tutorial button in each module for context-specific help</li>
            <li>Processing logs are automatically maintained</li>
        </ul>
        
        <p><i>Based on concepts from "Python for Astronomers"</i></p>
        """
        
        dialog = TutorialPopup("AstroLink Tutorial", content, self)
        dialog.exec()
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About AstroLink",
            """
            <h2>AstroLink v1.0.0</h2>
            <p>Your Intelligent Astronomical Laboratory</p>
            <p>An integrated desktop application for astronomical workflows.</p>
            <br>
            <p><b>Built with:</b></p>
            <ul>
                <li>Python & PySide6</li>
                <li>Astropy ecosystem</li>
                <li>Scientific Python libraries</li>
            </ul>
            <br>
            <p>© 2024 AstroLink Team<br>
            MIT License</p>
            """
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        reply = QMessageBox.question(
            self, "Quit AstroLink",
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
