"""Admin module initialization."""

from lta.modules.admin.system_monitor import (
    SystemMonitor,
    run_system_monitor,
)

__all__ = [
    "SystemMonitor",
    "run_system_monitor",
]
