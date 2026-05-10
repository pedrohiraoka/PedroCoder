"""System monitoring module for LTA.

Provides real-time system monitoring, resource tracking,
and administrative functions for Linux systems.
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lta.logger import setup_logger
from lta.utils.system import (
    get_system_info,
    get_resource_usage,
    get_top_processes,
    get_services_status,
    get_users,
    get_disk_partitions,
    format_bytes,
    format_uptime,
    SystemInfo,
    ResourceUsage,
)

logger = setup_logger(__name__)
console = Console()


class SystemMonitor:
    """Real-time system monitoring and administration."""

    def __init__(self) -> None:
        """Initialize the system monitor."""
        self._system_info: Optional[SystemInfo] = None
        self._last_usage: Optional[ResourceUsage] = None

    def get_overview(self) -> dict:
        """Get comprehensive system overview.

        Returns:
            Dictionary with system overview data.
        """
        logger.debug("Fetching system overview")
        
        self._system_info = get_system_info()
        self._last_usage = get_resource_usage()

        return {
            "system": self._system_info,
            "resources": self._last_usage,
            "processes": get_top_processes(limit=5),
            "users": get_users(),
            "disks": get_disk_partitions(),
        }

    def display_dashboard(self) -> None:
        """Display a system dashboard in the terminal."""
        console.clear()
        
        system_info = get_system_info()
        usage = get_resource_usage()
        processes = get_top_processes(limit=8)

        # Header
        header = Text()
        header.append("🖥️  ", style="bold")
        header.append(f"System Dashboard - {system_info.hostname}", style="bold blue")
        header.append("\n")
        header.append(f"{system_info.os_name} {system_info.os_version} | ", style="dim")
        header.append(f"Kernel: {system_info.kernel_version}", style="dim")
        console.print(Panel(header, style="bold"))

        # Resource usage grid
        cpu_bar = self._make_progress_bar(usage.cpu_percent, "CPU", "green")
        mem_bar = self._make_progress_bar(usage.memory_percent, "Memory", "blue")
        disk_bar = self._make_progress_bar(usage.disk_percent, "Disk", "yellow")

        resources_panel = Panel(
            f"{cpu_bar}\n{mem_bar}\n{disk_bar}\n\n"
            f"Load Average: {usage.load_average[0]:.2f}, {usage.load_average[1]:.2f}, {usage.load_average[2]:.2f}\n"
            f"Uptime: {format_uptime(system_info.uptime_seconds)}\n"
            f"Swap: {usage.swap_percent:.1f}% used",
            title="📊 Resource Usage",
            style="bold",
        )
        console.print(resources_panel)

        # Top processes table
        if processes:
            proc_table = Table(title="⚡ Top Processes by CPU", show_header=True, header_style="bold magenta")
            proc_table.add_column("PID", style="cyan", justify="right")
            proc_table.add_column("Name", style="green")
            proc_table.add_column("User", style="yellow")
            proc_table.add_column("CPU%", style="red", justify="right")
            proc_table.add_column("MEM%", style="blue", justify="right")
            proc_table.add_column("Command", style="white", overflow="ellipsis")

            for proc in processes:
                proc_table.add_row(
                    str(proc.pid),
                    proc.name[:20],
                    proc.username[:15],
                    f"{proc.cpu_percent:.1f}",
                    f"{proc.memory_percent:.1f}",
                    proc.cmdline[:40],
                )

            console.print(proc_table)

        console.print()

    def _make_progress_bar(self, percent: float, label: str, color: str) -> str:
        """Create a text-based progress bar.

        Args:
            percent: Percentage value (0-100).
            label: Label for the bar.
            color: Color name for the bar.

        Returns:
            Formatted progress bar string.
        """
        bar_width = 30
        filled = int(bar_width * percent / 100)
        empty = bar_width - filled

        bar = "█" * filled + "░" * empty
        return f"{label:8s} [{color}]{bar}[/{color}] {percent:5.1f}%"

    def display_memory_detail(self) -> None:
        """Display detailed memory information."""
        usage = get_resource_usage()
        
        console.print(Panel("[bold blue]Memory Details[/bold blue]", style="bold"))
        console.print(f"Total:   {usage.memory_total_gb:.2f} GB")
        console.print(f"Used:    {usage.memory_used_gb:.2f} GB ({usage.memory_percent:.1f}%)")
        console.print(f"Free:    {usage.memory_total_gb - usage.memory_used_gb:.2f} GB")
        console.print(f"Swap:    {usage.swap_percent:.1f}% used")
        console.print()

    def display_disk_detail(self) -> None:
        """Display detailed disk information."""
        partitions = get_disk_partitions()
        
        table = Table(title="💾 Disk Partitions", show_header=True, header_style="bold magenta")
        table.add_column("Device", style="cyan")
        table.add_column("Mount Point", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Total", justify="right", style="blue")
        table.add_column("Used", justify="right", style="red")
        table.add_column("Free", justify="right", style="white")
        table.add_column("Use%", justify="right", style="bold")

        for part in partitions:
            if part["total_gb"] is not None:
                use_style = "red" if part["percent_used"] > 90 else "yellow" if part["percent_used"] > 70 else "green"
                table.add_row(
                    part["device"],
                    part["mountpoint"],
                    part["fstype"],
                    f"{part['total_gb']:.1f} GB",
                    f"{part['used_gb']:.1f} GB",
                    f"{part['free_gb']:.1f} GB",
                    f"[{use_style}]{part['percent_used']:.1f}%[/{use_style}]",
                )

        console.print(table)
        console.print()

    def display_services(self, service_filter: Optional[str] = None) -> None:
        """Display systemd services status.

        Args:
            service_filter: Optional filter for service name.
        """
        services = get_services_status(service_filter)
        
        if not services:
            console.print("[yellow]No services found or systemctl not available[/yellow]")
            return

        table = Table(title="🔧 Running Services", show_header=True, header_style="bold magenta")
        table.add_column("Unit", style="cyan")
        table.add_column("Active", style="green")
        table.add_column("Sub", style="yellow")
        table.add_column("Description", style="white", overflow="ellipsis")

        for svc in services[:20]:  # Limit to 20 services
            table.add_row(
                svc["unit"],
                svc["active"],
                svc["sub"],
                svc["description"][:50],
            )

        console.print(table)
        console.print()

    def display_users(self) -> None:
        """Display logged-in users."""
        users = get_users()
        
        if not users:
            console.print("[yellow]No users currently logged in[/yellow]")
            return

        table = Table(title="👥 Logged-in Users", show_header=True, header_style="bold magenta")
        table.add_column("Username", style="cyan")
        table.add_column("Terminal", style="green")
        table.add_column("Host", style="yellow")
        table.add_column("Since", style="blue")

        for user in users:
            table.add_row(
                user["name"],
                user["terminal"] or "N/A",
                user["host"] or "local",
                user["started"].strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print()


def run_system_monitor(interactive: bool = True) -> None:
    """Run the system monitor.

    Args:
        interactive: If True, display interactive dashboard.
    """
    monitor = SystemMonitor()
    
    if interactive:
        monitor.display_dashboard()
    else:
        overview = monitor.get_overview()
        console.print(f"Hostname: {overview['system'].hostname}")
        console.print(f"OS: {overview['system'].os_name} {overview['system'].os_version}")
        console.print(f"CPU: {overview['resources'].cpu_percent:.1f}%")
        console.print(f"Memory: {overview['resources'].memory_percent:.1f}%")
        console.print(f"Disk: {overview['resources'].disk_percent:.1f}%")
