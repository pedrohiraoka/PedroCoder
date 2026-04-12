"""
AstroModel Module - Bayesian Modeling & Simulations

Provides tools for:
- Curve fitting with lmfit
- Bayesian inference
- N-body simulations with rebound
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QMessageBox, QTabWidget,
    QLineEdit, QComboBox
)
from PySide6.QtGui import QFont

from astrolink.core.logger import get_logger
from astrolink.gui.widgets import MplCanvas, TutorialPopup

logger = get_logger(__name__)


class ModelModule(QWidget):
    """
    AstroModel module widget.
    
    Provides interface for modeling and simulations.
    """
    
    def __init__(self, app_controller):
        super().__init__()
        self.app = app_controller
        
        self._init_ui()
        logger.info("Model module initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🧮 AstroModel - Modeling & Simulations")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Curve fitting tab
        fitting_tab = self._create_fitting_tab()
        tabs.addTab(fitting_tab, "Curve Fitting")
        
        # N-body simulation tab
        nbody_tab = self._create_nbody_tab()
        tabs.addTab(nbody_tab, "N-Body Simulation")
        
        layout.addWidget(tabs)
        
        # Tutorial button
        tutorial_btn = QPushButton("🎓 Tutorial")
        tutorial_btn.clicked.connect(self.show_tutorial)
        layout.addWidget(tutorial_btn)
        
        self.setLayout(layout)
    
    def _create_fitting_tab(self) -> QWidget:
        """Create curve fitting tab."""
        panel = QWidget()
        layout = QHBoxLayout()
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QFormLayout()
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Gaussian", "Lorentzian", "Polynomial", "Power Law"])
        model_layout.addRow("Model Type:", self.model_combo)
        
        fit_btn = QPushButton("Fit to Data")
        fit_btn.clicked.connect(self.fit_data)
        model_layout.addRow("", fit_btn)
        
        model_group.setLayout(model_layout)
        left_layout.addWidget(model_group)
        
        # Parameters display
        params_group = QGroupBox("Fitted Parameters")
        params_layout = QVBoxLayout()
        
        self.params_text = QLabel("No fit results yet")
        self.params_text.setStyleSheet("color: #666;")
        params_layout.addWidget(self.params_text)
        
        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # Right panel - Plot
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        self.fit_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        right_layout.addWidget(self.fit_canvas)
        
        right_panel.setLayout(right_layout)
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        panel.setLayout(layout)
        
        return panel
    
    def _create_nbody_tab(self) -> QWidget:
        """Create N-body simulation tab."""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Simulation controls
        sim_group = QGroupBox("Solar System Simulation")
        sim_layout = QHBoxLayout()
        
        run_sim_btn = QPushButton("Run Earth-Sun-Jupiter Simulation")
        run_sim_btn.clicked.connect(self.run_nbody_simulation)
        sim_layout.addWidget(run_sim_btn)
        
        sim_group.setLayout(sim_layout)
        layout.addWidget(sim_group)
        
        # Simulation canvas
        self.nbody_canvas = MplCanvas(self, width=6, height=5, dpi=100)
        layout.addWidget(self.nbody_canvas)
        
        panel.setLayout(layout)
        return panel
    
    def fit_data(self):
        """Fit a model to sample data."""
        try:
            import numpy as np
            from lmfit import Model
            
            # Generate sample data (in real use, load from analysis module)
            x = np.linspace(0, 10, 100)
            true_params = {'amplitude': 5, 'center': 5, 'sigma': 1}
            y_true = true_params['amplitude'] * np.exp(-((x - true_params['center']) ** 2) / (2 * true_params['sigma'] ** 2))
            y_noisy = y_true + np.random.normal(0, 0.3, size=x.shape)
            
            # Fit Gaussian model
            model_type = self.model_combo.currentText()
            
            if model_type == "Gaussian":
                def gaussian(x, amplitude, center, sigma):
                    return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))
                
                mod = Model(gaussian)
                params = mod.make_params(amplitude=4, center=4, sigma=1.5)
            
            result = mod.fit(y_noisy, params, x=x)
            
            # Display results
            self.params_text.setText(
                f"Amplitude: {result.params['amplitude'].value:.3f}\n"
                f"Center: {result.params['center'].value:.3f}\n"
                f"Sigma: {result.params['sigma'].value:.3f}\n"
                f"Chi-square: {result.chisqr:.3f}"
            )
            
            # Plot results
            self.fit_canvas.clear()
            ax = self.fit_canvas.axes
            
            ax.plot(x, y_noisy, 'bo', label='Data', markersize=3)
            ax.plot(x, y_true, 'g--', label='True', linewidth=2)
            ax.plot(x, result.best_fit, 'r-', label='Fit', linewidth=2)
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(f"{model_type} Fit")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            self.fit_canvas.draw()
            
            # Log processing
            self.app.add_processing_log(
                'model', 'curve_fit',
                outputs=['fit_results'],
                parameters={
                    'model': model_type,
                    'chi_square': float(result.chisqr)
                }
            )
            
            logger.info(f"Fitted {model_type} model")
            
        except ImportError:
            QMessageBox.warning(self, "Warning", "lmfit not available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fitting failed: {e}")
            logger.error(f"Fitting error: {e}")
    
    def run_nbody_simulation(self):
        """Run a simple N-body simulation."""
        try:
            import rebound
            import numpy as np
            
            # Create simulation
            sim = rebound.Simulation()
            sim.units = ('AU', 'yr', 'Msun')
            
            # Add Sun
            sim.add(m=1.0)
            
            # Add Earth
            sim.add(m=3e-6, a=1.0, e=0.017)
            
            # Add Jupiter
            sim.add(m=9.5e-4, a=5.2, e=0.048)
            
            # Integrate
            times = np.linspace(0, 12, 100)  # 12 years
            earth_x, earth_y = [], []
            jup_x, jup_y = [], []
            
            for t in times:
                sim.integrate(t)
                earth_x.append(sim.particles[1].x)
                earth_y.append(sim.particles[1].y)
                jup_x.append(sim.particles[2].x)
                jup_y.append(sim.particles[2].y)
            
            # Plot orbits
            self.nbody_canvas.clear()
            ax = self.nbody_canvas.axes
            
            ax.plot(earth_x, earth_y, 'b-', label='Earth', linewidth=1)
            ax.plot(jup_x, jup_y, 'r-', label='Jupiter', linewidth=2)
            ax.plot(0, 0, 'yo', markersize=15, label='Sun')
            
            ax.set_xlabel("X (AU)")
            ax.set_ylabel("Y (AU)")
            ax.set_title("Earth-Sun-Jupiter Orbits (12 years)")
            ax.legend()
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            
            self.nbody_canvas.draw()
            
            # Log processing
            self.app.add_processing_log(
                'model', 'nbody_simulation',
                outputs=['orbit_data'],
                parameters={
                    'bodies': 3,
                    'duration_years': 12
                }
            )
            
            logger.info("Ran N-body simulation")
            
        except ImportError:
            QMessageBox.warning(self, "Warning", "rebound not available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Simulation failed: {e}")
            logger.error(f"N-body error: {e}")
    
    def show_tutorial(self):
        """Show tutorial for this module."""
        content = """
        <h2>AstroModel Tutorial</h2>
        <p>This module provides modeling and simulation tools.</p>
        
        <h3>Curve Fitting:</h3>
        <ol>
            <li><b>Select model</b> - Choose from Gaussian, Lorentzian, etc.</li>
            <li><b>Fit to data</b> - Click to fit the model</li>
            <li><b>Review parameters</b> - Check fitted values and statistics</li>
        </ol>
        
        <h3>N-Body Simulation:</h3>
        <ol>
            <li><b>Run simulation</b> - Execute Earth-Sun-Jupiter simulation</li>
            <li><b>View orbits</b> - See orbital paths over time</li>
        </ol>
        
        <h3>Tips:</h3>
        <ul>
            <li>Good initial guesses improve fitting convergence</li>
            <li>Check chi-square to assess fit quality</li>
            <li>N-body uses REBOUND library for accurate integration</li>
        </ul>
        """
        dialog = TutorialPopup("Model Module Tutorial", content, self)
        dialog.exec()
