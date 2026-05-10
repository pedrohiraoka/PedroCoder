"""System utilities for LTA.

Provides system monitoring, distro detection, process management,
and privilege checking functionality.
"""

import os
import platform
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil

from lta.logger import setup_logger
from lta.utils.shell import run_command, is_root

logger = setup_logger(__name__)


@dataclass
class SystemInfo:
    """System information snapshot."""

    hostname: str
    os_name: str
    os_version: str
    kernel_version: str
    architecture: str
    cpu_count: int
    total_memory_gb: float
    boot_time: datetime
    uptime_seconds: float


@dataclass
class ResourceUsage:
    """Current resource usage metrics."""

    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    swap_percent: float
    load_average: tuple[float, float, float]


@dataclass
class ProcessInfo:
    """Process information."""

    pid: int
    name: str
    username: str
    status: str
    cpu_percent: float
    memory_percent: float
    cmdline: str
    num_threads: int


def get_system_info() -> SystemInfo:
    """Get comprehensive system information.

    Returns:
        SystemInfo object with system details.
    """
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = (datetime.now() - boot_time).total_seconds()

    os_info = get_distro_info()

    return SystemInfo(
        hostname=platform.node(),
        os_name=os_info["name"],
        os_version=os_info["version"],
        kernel_version=platform.release(),
        architecture=platform.machine(),
        cpu_count=psutil.cpu_count(logical=True) or 1,
        total_memory_gb=psutil.virtual_memory().total / (1024**3),
        boot_time=boot_time,
        uptime_seconds=uptime,
    )


def get_resource_usage() -> ResourceUsage:
    """Get current resource usage metrics.

    Returns:
        ResourceUsage object with current metrics.
    """
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    swap = psutil.swap_memory()
    load_avg = psutil.getloadavg()

    return ResourceUsage(
        cpu_percent=psutil.cpu_percent(interval=0.1),
        memory_percent=memory.percent,
        memory_used_gb=memory.used / (1024**3),
        memory_total_gb=memory.total / (1024**3),
        disk_percent=disk.percent,
        disk_used_gb=disk.used / (1024**3),
        disk_total_gb=disk.total / (1024**3),
        swap_percent=swap.percent,
        load_average=load_avg,
    )


def get_top_processes(limit: int = 10) -> list[ProcessInfo]:
    """Get top processes by CPU usage.

    Args:
        limit: Maximum number of processes to return.

    Returns:
        List of ProcessInfo objects sorted by CPU usage.
    """
    processes = []

    for proc in psutil.process_iter(["pid", "name", "username", "status", "cpu_percent", "memory_percent", "cmdline", "num_threads"]):
        try:
            info = proc.info
            cmdline = " ".join(info["cmdline"]) if info["cmdline"] else info["name"]
            processes.append(ProcessInfo(
                pid=info["pid"],
                name=info["name"],
                username=info["username"] or "unknown",
                status=info["status"],
                cpu_percent=info["cpu_percent"] or 0.0,
                memory_percent=info["memory_percent"] or 0.0,
                cmdline=cmdline[:100],  # Truncate long command lines
                num_threads=info["num_threads"] or 1,
            ))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda p: p.cpu_percent, reverse=True)
    return processes[:limit]


def get_distro_info() -> dict[str, str]:
    """Detect Linux distribution information.

    Returns:
        Dictionary with 'name', 'version', and 'id' keys.
    """
    distro_id = "unknown"
    distro_name = "Linux"
    distro_version = "unknown"

    os_release_path = Path("/etc/os-release")
    if os_release_path.exists():
        try:
            with open(os_release_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("ID="):
                        distro_id = line.split("=", 1)[1].strip('"')
                    elif line.startswith("NAME="):
                        distro_name = line.split("=", 1)[1].strip('"')
                    elif line.startswith("VERSION_ID="):
                        distro_version = line.split("=", 1)[1].strip('"')
        except OSError:
            pass

    if distro_id == "unknown":
        distro_id = platform.system().lower()

    return {
        "id": distro_id,
        "name": distro_name,
        "version": distro_version,
    }


def get_package_manager() -> Optional[str]:
    """Detect the available package manager.

    Returns:
        Package manager command name or None if not found.
    """
    distro_info = get_distro_info()
    distro_id = distro_info["id"]

    package_managers = {
        "debian": ["apt", "apt-get", "dpkg"],
        "ubuntu": ["apt", "apt-get", "dpkg"],
        "fedora": ["dnf", "yum", "rpm"],
        "rhel": ["dnf", "yum", "rpm"],
        "centos": ["dnf", "yum", "rpm"],
        "arch": ["pacman", "yay", "paru"],
        "opensuse": ["zypper", "rpm"],
        "suse": ["zypper", "rpm"],
        "alpine": ["apk"],
        "gentoo": ["emerge", "portage"],
    }

    for manager in package_managers.get(distro_id, []):
        if _command_exists(manager):
            return manager

    for managers in package_managers.values():
        for manager in managers:
            if _command_exists(manager):
                return manager

    return None


def _command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH.

    Args:
        cmd: Command name to check.

    Returns:
        True if command exists.
    """
    return os.path.isfile(f"/usr/bin/{cmd}") or os.path.isfile(f"/bin/{cmd}")


def get_services_status(service_name: Optional[str] = None) -> list[dict]:
    """Get systemd services status.

    Args:
        service_name: Optional specific service name to query.

    Returns:
        List of service status dictionaries.
    """
    if not _command_exists("systemctl"):
        logger.warning("systemctl not found, cannot query services")
        return []

    cmd = ["systemctl", "list-units", "--type=service", "--state=running", "--no-pager"]
    if service_name:
        cmd = ["systemctl", "status", service_name, "--no-pager"]

    result = run_command(cmd)

    services = []
    if result.success:
        for line in result.stdout.splitlines():
            if line.strip() and not line.startswith("●") and "loaded" not in line.lower():
                parts = line.split()
                if len(parts) >= 4:
                    services.append({
                        "unit": parts[0],
                        "load": parts[1],
                        "active": parts[2],
                        "sub": parts[3],
                        "description": " ".join(parts[4:]) if len(parts) > 4 else "",
                    })

    return services


def get_users() -> list[dict]:
    """Get logged-in users information.

    Returns:
        List of user information dictionaries.
    """
    users = []
    for user in psutil.users():
        users.append({
            "name": user.name,
            "terminal": user.terminal,
            "host": user.host,
            "started": datetime.fromtimestamp(user.started),
        })
    return users


def get_disk_partitions() -> list[dict]:
    """Get disk partition information.

    Returns:
        List of partition information dictionaries.
    """
    partitions = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            partitions.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "opts": partition.opts,
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3),
                "percent_used": usage.percent,
            })
        except PermissionError:
            partitions.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "opts": partition.opts,
                "total_gb": None,
                "used_gb": None,
                "free_gb": None,
                "percent_used": None,
            })
    return partitions


def get_network_connections() -> list[dict]:
    """Get active network connections.

    Returns:
        List of connection information dictionaries.
    """
    connections = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == "LISTEN" or conn.status == "ESTABLISHED":
            connections.append({
                "proto": "tcp" if conn.type == psutil.SOCK_STREAM else "udp",
                "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                "status": conn.status,
                "pid": conn.pid,
            })
    return connections


def kill_process(pid: int, signal: int = 15) -> bool:
    """Kill a process by PID.

    Args:
        pid: Process ID to kill.
        signal: Signal to send (15=SIGTERM, 9=SIGKILL).

    Returns:
        True if process was killed successfully.

    Raises:
        PermissionError: If insufficient privileges.
        ProcessLookupError: If process doesn't exist.
    """
    try:
        os.kill(pid, signal)
        logger.info(f"Sent signal {signal} to process {pid}")
        return True
    except PermissionError:
        logger.error(f"Insufficient privileges to kill process {pid}")
        raise
    except ProcessLookupError:
        logger.warning(f"Process {pid} not found")
        raise


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable string.

    Args:
        bytes_value: Number of bytes.

    Returns:
        Formatted string (e.g., "1.5 GB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_uptime(seconds: float) -> str:
    """Format uptime seconds into human-readable string.

    Args:
        seconds: Uptime in seconds.

    Returns:
        Formatted string (e.g., "2 days, 3 hours, 45 minutes").
    """
    intervals = [
        ("day", 86400),
        ("hour", 3600),
        ("minute", 60),
        ("second", 1),
    ]

    parts = []
    for name, count in intervals:
        value = int(seconds // count)
        if value:
            parts.append(f"{value} {name}" + ("s" if value != 1 else ""))
            seconds %= count

    return ", ".join(parts) if parts else "0 seconds"
