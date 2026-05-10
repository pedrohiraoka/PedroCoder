#!/usr/bin/env python3
"""Linux Terminal Assistant (LTA) - Main CLI entrypoint.

A professional CLI/TUI assistant for Linux system administrators and developers.
Provides system monitoring, diagnostics, media downloading, and automation tools.

Usage:
    lta                      # Interactive mode
    lta ip                   # Show public IP
    lta admin monitor        # System monitoring dashboard
    lta download <url>       # Download media
    lta --help               # Show help
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from lta import __version__
from lta.config import get_config, Config
from lta.logger import setup_logger, get_log_level_from_string
from lta.utils.network import IPResolver, ping, dns_lookup
from lta.utils.system import get_system_info, get_resource_usage, format_uptime
from lta.modules.admin.system_monitor import run_system_monitor
from lta.modules.downloader.yt_dlp_wrapper import run_downloader, YtDlpError

# Initialize console and logger
console = Console()
logger = setup_logger(__name__)

# Create Typer app
app = typer.Typer(
    name="lta",
    help="Linux Terminal Assistant - Professional CLI/TUI for Linux administration",
    epilog="For more information, visit: https://github.com/example/linux-terminal-assistant",
    no_args_is_help=False,
)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]LTA[/bold blue] v{__version__}")
        console.print("Linux Terminal Assistant")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose output (DEBUG level)",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Custom configuration file path",
    ),
    no_colors: bool = typer.Option(
        False,
        "--no-colors",
        envvar="NO_COLOR",
        help="Disable colored output",
    ),
) -> None:
    """Main callback executed before any subcommand."""
    log_level = "DEBUG" if verbose else "INFO"
    logger.setLevel(get_log_level_from_string(log_level))
    
    if no_colors:
        console.no_color = True


@app.command()
def ip(
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        "-n",
        help="Ignore cache and fetch fresh IP",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output in JSON format",
    ),
) -> None:
    """Show your public IP address with automatic fallback between backends."""
    try:
        resolver = IPResolver()
        result = resolver.get_public_ip(use_cache=not no_cache)
        
        if json_output:
            import json
            console.print(json.dumps({
                "ip": result.ip,
                "source": result.source,
                "timestamp": result.timestamp,
            }))
        else:
            console.print(Panel(
                f"[bold cyan]{result.ip}[/bold cyan]\n"
                f"[dim]Source: {result.source}[/dim]",
                title="🌐 Public IP Address",
                style="blue",
            ))
    except Exception as e:
        console.print(f"[red]Error fetching IP: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ping_host(
    host: str = typer.Argument(..., help="Hostname or IP to ping"),
    count: int = typer.Option(4, "--count", "-c", help="Number of packets"),
    timeout: int = typer.Option(5, "--timeout", "-t", help="Timeout per packet"),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output in JSON format",
    ),
) -> None:
    """Ping a host and display latency statistics."""
    from lta.utils.network import ping as network_ping
    
    console.print(f"Pinging [cyan]{host}[/cyan]...")
    stats = network_ping(host, count=count, timeout=timeout)
    
    if json_output:
        import json
        console.print(json.dumps(stats, indent=2))
    elif stats["success"]:
        console.print(Panel(
            f"Packets: {stats['packets_received']}/{stats['packets_sent']} received\n"
            f"Loss: {stats['packet_loss_percent']:.1f}%\n"
            f"RTT: {stats['min_rtt_ms']:.1f}/{stats['avg_rtt_ms']:.1f}/{stats['max_rtt_ms']:.1f} ms",
            title=f"📡 Ping Results - {host}",
            style="green" if stats["packet_loss_percent"] < 50 else "yellow",
        ))
    else:
        console.print(f"[red]✗ Ping failed - host unreachable[/red]")
        raise typer.Exit(1)


@app.command()
def dns(
    hostname: str = typer.Argument(..., help="Hostname to resolve"),
    record_type: str = typer.Option("A", "--type", "-t", help="DNS record type"),
) -> None:
    """Perform DNS lookup for a hostname."""
    from lta.utils.network import dns_lookup as network_dns
    
    try:
        records = network_dns(hostname, record_type)
        
        if records:
            console.print(f"[bold]{hostname}[/bold] ({record_type}):")
            for record in records:
                console.print(f"  [cyan]{record}[/cyan]")
        else:
            console.print(f"[yellow]No {record_type} records found for {hostname}[/yellow]")
    except Exception as e:
        console.print(f"[red]DNS lookup failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output in JSON format",
    ),
) -> None:
    """Quick system status overview."""
    try:
        system_info = get_system_info()
        usage = get_resource_usage()
        
        if json_output:
            import json
            console.print(json.dumps({
                "hostname": system_info.hostname,
                "os": f"{system_info.os_name} {system_info.os_version}",
                "kernel": system_info.kernel_version,
                "cpu_percent": usage.cpu_percent,
                "memory_percent": usage.memory_percent,
                "disk_percent": usage.disk_percent,
                "uptime_seconds": system_info.uptime_seconds,
            }, indent=2))
        else:
            console.print(Panel(
                f"[bold]{system_info.hostname}[/bold]\n"
                f"{system_info.os_name} {system_info.os_version} | Kernel: {system_info.kernel_version}\n"
                f"Uptime: {format_uptime(system_info.uptime_seconds)}\n\n"
                f"CPU: {usage.cpu_percent:.1f}% | "
                f"Memory: {usage.memory_percent:.1f}% | "
                f"Disk: {usage.disk_percent:.1f}%",
                title="🖥️ System Status",
                style="blue",
            ))
    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def monitor(
    interactive: bool = typer.Option(
        True,
        "--interactive",
        "-i",
        help="Run in interactive mode",
    ),
) -> None:
    """Launch system monitoring dashboard."""
    run_system_monitor(interactive=interactive)


@app.command()
def download(
    url: str = typer.Argument(..., help="Media URL to download"),
    audio_only: bool = typer.Option(
        False,
        "--audio",
        "-a",
        help="Download audio only",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory",
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired format (mp3, mp4, etc.)",
    ),
    playlist: bool = typer.Option(
        False,
        "--playlist",
        "-p",
        help="Download entire playlist",
    ),
) -> None:
    """Download media using yt-dlp with progress tracking."""
    try:
        run_downloader(
            url=url,
            audio_only=audio_only,
            output_dir=output_dir,
            format=format,
            playlist=playlist,
        )
    except YtDlpError as e:
        console.print(f"[red]Download error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def info(
    full: bool = typer.Option(
        False,
        "--full",
        "-f",
        help="Show full detailed information",
    ),
) -> None:
    """Display comprehensive system information."""
    from lta.utils.system import (
        get_distro_info,
        get_package_manager,
        get_users,
        get_disk_partitions,
    )
    
    system_info = get_system_info()
    distro = get_distro_info()
    pkg_manager = get_package_manager()
    
    console.print(Panel("[bold]System Information[/bold]", style="bold magenta"))
    
    console.print(f"\n[bold]Hostname:[/bold] {system_info.hostname}")
    console.print(f"[bold]OS:[/bold] {distro['name']} {distro['version']}")
    console.print(f"[bold]Kernel:[/bold] {system_info.kernel_version}")
    console.print(f"[bold]Architecture:[/bold] {system_info.architecture}")
    console.print(f"[bold]CPU Cores:[/bold] {system_info.cpu_count}")
    console.print(f"[bold]Memory:[/bold] {system_info.total_memory_gb:.2f} GB")
    console.print(f"[bold]Package Manager:[/bold] {pkg_manager or 'Unknown'}")
    console.print(f"[bold]Boot Time:[/bold] {system_info.boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"[bold]Uptime:[/bold] {format_uptime(system_info.uptime_seconds)}")
    
    if full:
        console.print("\n[bold]Disk Partitions:[/bold]")
        for part in get_disk_partitions():
            if part["mountpoint"] == "/":
                console.print(f"  {part['device']} → {part['mountpoint']} "
                            f"({part['percent_used']:.1f}% used)")
        
        console.print("\n[bold]Logged-in Users:[/bold]")
        users = get_users()
        if users:
            for user in users:
                console.print(f"  {user['name']} on {user['terminal'] or 'N/A'} "
                            f"since {user['started'].strftime('%H:%M')}")
        else:
            console.print("  No users logged in")


@app.command()
def check(
    tool: str = typer.Argument(
        "all",
        help="Tool to check (all, yt-dlp, fzf, jq, rg, bat, docker)",
    ),
) -> None:
    """Check availability of external tools and dependencies."""
    from lta.utils.shell import get_available_commands, which
    
    tools_to_check = {
        "yt-dlp": "Media downloading",
        "fzf": "Interactive search",
        "jq": "JSON processing",
        "rg": "Fast text search (ripgrep)",
        "bat": "Syntax-highlighted cat",
        "docker": "Container management",
        "podman": "Container management (rootless)",
        "tmux": "Terminal multiplexer",
        "dig": "DNS lookup",
        "traceroute": "Network tracing",
    }
    
    if tool != "all":
        tools_to_check = {tool: tools_to_check.get(tool, "Unknown")}
    
    available = get_available_commands(list(tools_to_check.keys()))
    
    console.print("\n[bold]External Tools Status[/bold]\n")
    
    all_installed = True
    for cmd, description in tools_to_check.items():
        status = "[green]✓[/green]" if available.get(cmd) else "[red]✗[/red]"
        if not available.get(cmd):
            all_installed = False
        console.print(f"  {status} [cyan]{cmd:15s}[/cyan] - {description}")
    
    console.print()
    if all_installed:
        console.print("[green]All tools are installed![/green]")
    else:
        console.print("[yellow]Some tools are missing. Install them for full functionality.[/yellow]")
        console.print("\n[dim]Installation hints:[/dim]")
        console.print("  Ubuntu/Debian: sudo apt install yt-dlp fzf jq ripgrep bat docker.io")
        console.print("  Fedora: sudo dnf install yt-dlp fzf jq ripgrep bat docker")
        console.print("  Arch: sudo pacman -S yt-dlp fzf jq ripgrep bat docker")


@app.command()
def interactive() -> None:
    """Launch interactive TUI mode (alias for running 'lta' without arguments)."""
    launch_interactive()


def launch_interactive() -> None:
    """Launch the interactive menu interface."""
    from rich.menu import Menu
    from rich.prompt import Prompt
    
    console.clear()
    console.print(Panel.fit(
        "[bold blue]🐧 Linux Terminal Assistant[/bold blue]\n"
        f"[dim]Version {__version__}[/dim]",
        style="bold",
    ))
    console.print()
    
    while True:
        console.print("\n[bold]Main Menu[/bold]\n")
        console.print("  [cyan]1[/cyan]. System Monitor")
        console.print("  [cyan]2[/cyan]. Quick Status")
        console.print("  [cyan]3[/cyan]. Public IP")
        console.print("  [cyan]4[/cyan]. Network Diagnostics")
        console.print("  [cyan]5[/cyan]. Download Media")
        console.print("  [cyan]6[/cyan]. System Info")
        console.print("  [cyan]7[/cyan]. Check Tools")
        console.print("  [cyan]0[/cyan]. Exit")
        console.print()
        
        choice = Prompt.ask("Select option", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="0")
        
        try:
            if choice == "0":
                console.print("[yellow]Goodbye![/yellow]")
                break
            elif choice == "1":
                run_system_monitor(interactive=True)
            elif choice == "2":
                invoke_command("status")
            elif choice == "3":
                invoke_command("ip")
            elif choice == "4":
                host = Prompt.ask("Enter hostname to ping", default="google.com")
                invoke_command("ping-host", host)
            elif choice == "5":
                url = Prompt.ask("Enter media URL")
                audio = Prompt.ask("Audio only?", choices=["y", "n"], default="n")
                invoke_command("download", url, audio_only=(audio.lower() == "y"))
            elif choice == "6":
                invoke_command("info", full=True)
            elif choice == "7":
                invoke_command("check")
            
            if choice != "1":
                Prompt.ask("\nPress Enter to continue")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            continue
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            Prompt.ask("Press Enter to continue")


def invoke_command(name: str, *args, **kwargs) -> None:
    """Invoke a Typer command programmatically."""
    from typer.main import get_command
    
    command = app.registered_commands
    for cmd in command:
        if cmd.name == name:
            cmd.callback(*args, **kwargs)
            return
    
    raise ValueError(f"Command {name} not found")


# Default command when no subcommand is given
@app.command()
def default() -> None:
    """Default action - launch interactive mode."""
    launch_interactive()


if __name__ == "__main__":
    app()
