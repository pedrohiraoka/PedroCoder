"""
Project state management for AstroLink.

Handles saving and loading project state (.astrolink files),
including input files, parameters, intermediate results, and processing history.
"""

import json
import pickle
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

from astrolink.core.logger import get_logger


logger = get_logger(__name__)


@dataclass
class ProcessingStep:
    """Represents a single step in the processing pipeline."""
    module: str
    action: str
    timestamp: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ProjectState:
    """Complete state of an AstroLink project."""
    name: str
    created: str
    modified: str
    version: str = "1.0"
    modules_state: Dict[str, Any] = field(default_factory=dict)
    processing_history: List[ProcessingStep] = field(default_factory=list)
    file_paths: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Project:
    """
    Manages project state for AstroLink sessions.
    
    Supports saving/loading to .astrolink format (ZIP-based),
    tracking processing history, and managing cross-module data flow.
    """
    
    def __init__(self, name: str = "Untitled"):
        """
        Initialize a new project.
        
        Args:
            name: Project name
        """
        self.name = name
        self.created = datetime.now().isoformat()
        self.modified = self.created
        self.version = "1.0"
        self.modules_state: Dict[str, Any] = {}
        self.processing_history: List[ProcessingStep] = []
        self.file_paths: Dict[str, List[str]] = {}
        self.metadata: Dict[str, Any] = {}
        self._current_file: Optional[Path] = None
        
        logger.info(f"Created new project: {name}")
    
    def add_processing_step(self, module: str, action: str, 
                           parameters: Dict[str, Any] = None,
                           inputs: List[str] = None,
                           outputs: List[str] = None,
                           success: bool = True,
                           error_message: str = None):
        """
        Record a processing step in the project history.
        
        Args:
            module: Module name (e.g., 'observe', 'reduce')
            action: Action performed (e.g., 'reduction', 'photometry')
            parameters: Parameters used in the step
            inputs: Input files/data
            outputs: Output files/data
            success: Whether the step succeeded
            error_message: Error message if failed
        """
        step = ProcessingStep(
            module=module,
            action=action,
            timestamp=datetime.now().isoformat(),
            parameters=parameters or {},
            inputs=inputs or [],
            outputs=outputs or [],
            success=success,
            error_message=error_message
        )
        self.processing_history.append(step)
        self.modified = datetime.now().isoformat()
        logger.debug(f"Added processing step: {module}.{action}")
    
    def set_module_state(self, module: str, state: Dict[str, Any]):
        """
        Save state for a specific module.
        
        Args:
            module: Module name
            state: State dictionary to save
        """
        self.modules_state[module] = state
        self.modified = datetime.now().isoformat()
        logger.debug(f"Saved state for module: {module}")
    
    def get_module_state(self, module: str) -> Dict[str, Any]:
        """
        Retrieve state for a specific module.
        
        Args:
            module: Module name
            
        Returns:
            Module state dictionary
        """
        return self.modules_state.get(module, {})
    
    def add_file_paths(self, category: str, paths: List[str]):
        """
        Add file paths to the project.
        
        Args:
            category: Category name (e.g., 'bias', 'dark', 'flat', 'science')
            paths: List of file paths
        """
        if category not in self.file_paths:
            self.file_paths[category] = []
        self.file_paths[category].extend(paths)
        self.modified = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project state to dictionary."""
        return {
            'name': self.name,
            'created': self.created,
            'modified': self.modified,
            'version': self.version,
            'modules_state': self.modules_state,
            'processing_history': [asdict(step) for step in self.processing_history],
            'file_paths': self.file_paths,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create Project instance from dictionary."""
        project = cls(name=data.get('name', 'Untitled'))
        project.created = data.get('created', datetime.now().isoformat())
        project.modified = data.get('modified', project.created)
        project.version = data.get('version', '1.0')
        project.modules_state = data.get('modules_state', {})
        project.processing_history = [
            ProcessingStep(**step) for step in data.get('processing_history', [])
        ]
        project.file_paths = data.get('file_paths', {})
        project.metadata = data.get('metadata', {})
        return project
    
    def save(self, filepath: str, include_data: bool = False):
        """
        Save project to .astrolink file.
        
        Args:
            filepath: Path to save project file
            include_data: If True, include binary data in the archive
        """
        filepath = Path(filepath)
        if not filepath.suffix == '.astrolink':
            filepath = filepath.with_suffix('.astrolink')
        
        self._current_file = filepath
        
        # Create ZIP archive
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Save project metadata
            project_json = json.dumps(self.to_dict(), indent=2)
            zf.writestr('project.json', project_json)
            
            # Optionally include serialized module state data
            if include_data:
                for module_name, state in self.modules_state.items():
                    # Serialize non-serializable objects with pickle
                    try:
                        data_pickle = pickle.dumps(state)
                        zf.writestr(f'data/{module_name}.pkl', data_pickle)
                    except Exception as e:
                        logger.warning(f"Could not serialize {module_name} data: {e}")
        
        logger.info(f"Saved project to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'Project':
        """
        Load project from .astrolink file.
        
        Args:
            filepath: Path to project file
            
        Returns:
            Loaded Project instance
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Project file not found: {filepath}")
        
        with zipfile.ZipFile(filepath, 'r') as zf:
            # Load project metadata
            with zf.open('project.json') as f:
                project_data = json.load(f)
            
            project = cls.from_dict(project_data)
            project._current_file = filepath
            
            # Load serialized data if available
            for info in zf.infolist():
                if info.filename.startswith('data/') and info.filename.endswith('.pkl'):
                    module_name = Path(info.filename).stem
                    try:
                        with zf.open(info.filename) as f:
                            data = pickle.load(f)
                        project.modules_state[module_name] = data
                    except Exception as e:
                        logger.warning(f"Could not load {module_name} data: {e}")
        
        logger.info(f"Loaded project from {filepath}")
        return project
    
    def export_log(self, filepath: str, format: str = 'txt'):
        """
        Export processing log to file.
        
        Args:
            filepath: Output file path
            format: Output format ('txt', 'json', 'csv')
        """
        filepath = Path(filepath)
        
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump([asdict(step) for step in self.processing_history], f, indent=2)
        
        elif format == 'csv':
            import csv
            with open(filepath, 'w', newline='') as f:
                if self.processing_history:
                    writer = csv.DictWriter(f, fieldnames=asdict(self.processing_history[0]).keys())
                    writer.writeheader()
                    for step in self.processing_history:
                        writer.writerow(asdict(step))
        
        else:  # txt format
            with open(filepath, 'w') as f:
                f.write(f"AstroLink Processing Log\n")
                f.write(f"Project: {self.name}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                
                for step in self.processing_history:
                    status = "✓" if step.success else "✗"
                    f.write(f"[{step.timestamp}] {status} {step.module}.{step.action}\n")
                    if step.parameters:
                        f.write(f"    Parameters: {step.parameters}\n")
                    if step.inputs:
                        f.write(f"    Inputs: {', '.join(step.inputs)}\n")
                    if step.outputs:
                        f.write(f"    Outputs: {', '.join(step.outputs)}\n")
                    if step.error_message:
                        f.write(f"    Error: {step.error_message}\n")
                    f.write("\n")
        
        logger.info(f"Exported processing log to {filepath}")
