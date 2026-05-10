"""Downloader module for LTA using yt-dlp.

Provides media download functionality with progress tracking,
format selection, and playlist support.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from lta.config import DownloaderConfig
from lta.logger import setup_logger
from lta.utils.shell import run_command, which, ShellError

logger = setup_logger(__name__)
console = Console()


@dataclass
class MediaInfo:
    """Information about downloadable media."""

    title: str
    url: str
    duration_seconds: Optional[int] = None
    formats: list[dict] = field(default_factory=list)
    thumbnail_url: Optional[str] = None
    uploader: Optional[str] = None
    is_playlist: bool = False
    playlist_count: Optional[int] = None


@dataclass
class DownloadProgress:
    """Download progress information."""

    filename: str
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_bps: float = 0.0
    eta_seconds: float = 0.0
    percent: float = 0.0
    status: str = "downloading"


class YtDlpError(Exception):
    """Exception raised for yt-dlp related errors."""

    pass


class MediaDownloader:
    """Media downloader using yt-dlp backend."""

    def __init__(self, config: Optional[DownloaderConfig] = None) -> None:
        """Initialize the media downloader.

        Args:
            config: Downloader configuration. Uses defaults if not provided.
        """
        self.config = config or DownloaderConfig()
        self._yt_dlp_path: Optional[str] = None
        self._check_yt_dlp()

    def _check_yt_dlp(self) -> None:
        """Check if yt-dlp is available."""
        self._yt_dlp_path = which("yt-dlp")
        if not self._yt_dlp_path:
            logger.warning("yt-dlp not found in PATH")
            raise YtDlpError(
                "yt-dlp is required for downloads. Install it with:\n"
                "  pip install yt-dlp\n"
                "  or visit: https://github.com/yt-dlp/yt-dlp#installation"
            )

    def validate_url(self, url: str) -> bool:
        """Validate a media URL.

        Args:
            url: URL to validate.

        Returns:
            True if URL appears valid.
        """
        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        
        if not url_pattern.match(url):
            return False

        # Check for common video platforms
        supported_domains = [
            "youtube.com", "youtu.be", "vimeo.com", "twitch.tv",
            "twitter.com", "tiktok.com", "instagram.com",
        ]
        
        for domain in supported_domains:
            if domain in url.lower():
                return True

        # Allow any HTTP(S) URL - yt-dlp supports many sites
        return True

    def get_media_info(self, url: str) -> MediaInfo:
        """Get information about media without downloading.

        Args:
            url: Media URL.

        Returns:
            MediaInfo object with metadata.

        Raises:
            YtDlpError: If URL is invalid or info cannot be retrieved.
        """
        if not self.validate_url(url):
            raise YtDlpError(f"Invalid URL: {url}")

        cmd = [
            self._yt_dlp_path,
            "--no-download",
            "--print-json",
            "--no-warnings",
            url,
        ]

        result = run_command(cmd, timeout=30.0)

        if not result.success:
            raise YtDlpError(f"Failed to get media info: {result.stderr}")

        try:
            import json
            data = json.loads(result.stdout)
            
            return MediaInfo(
                title=data.get("title", "Unknown"),
                url=url,
                duration_seconds=data.get("duration"),
                formats=data.get("formats", []),
                thumbnail_url=data.get("thumbnail"),
                uploader=data.get("uploader"),
                is_playlist=data.get("_type") == "playlist",
                playlist_count=data.get("playlist_count"),
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise YtDlpError(f"Failed to parse media info: {e}") from e

    def download(
        self,
        url: str,
        output_dir: Optional[Path] = None,
        audio_only: bool = False,
        format: Optional[str] = None,
        playlist: bool = False,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """Download media from URL.

        Args:
            url: Media URL to download.
            output_dir: Directory to save downloaded file.
            audio_only: If True, extract audio only.
            format: Specific format to download (e.g., 'mp4', 'mp3').
            playlist: If True, download entire playlist.
            progress_callback: Optional callback for progress updates.

        Returns:
            Path to downloaded file.

        Raises:
            YtDlpError: If download fails.
        """
        if not self.validate_url(url):
            raise YtDlpError(f"Invalid URL: {url}")

        output_dir = output_dir or Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            self._yt_dlp_path,
            "--no-warnings",
            "--newline",
        ]

        # Output template
        output_template = str(output_dir / self.config.output_template)
        cmd.extend(["-o", output_template])

        # Format selection
        if audio_only:
            audio_format = format or self.config.default_audio_format
            cmd.extend([
                "-x",  # Extract audio
                "--audio-format", audio_format,
            ])
        else:
            video_format = format or self.config.default_video_format
            if format:
                cmd.extend(["-f", f"bestvideo[ext={video_format}]+bestaudio/best"])

        # Playlist handling
        if not playlist:
            cmd.append("--no-playlist")
        else:
            cmd.append("--yes-playlist")

        # Rate limiting
        if self.config.rate_limit:
            cmd.extend(["--limit-rate", self.config.rate_limit])

        # Prefer free formats
        if self.config.prefer_free_formats:
            cmd.append("--prefer-free-formats")

        cmd.append(url)

        logger.info(f"Downloading: {url}")
        logger.debug(f"Command: {' '.join(cmd)}")

        # Run with progress parsing
        result = run_command(cmd, timeout=None, capture_output=True)

        if not result.success:
            raise YtDlpError(f"Download failed: {result.stderr}")

        # Find downloaded file
        downloaded_files = list(output_dir.glob("*"))
        if downloaded_files:
            latest = max(downloaded_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Downloaded: {latest}")
            return latest

        raise YtDlpError("Download completed but file not found")

    def download_with_progress(
        self,
        url: str,
        output_dir: Optional[Path] = None,
        audio_only: bool = False,
        format: Optional[str] = None,
    ) -> Path:
        """Download media with Rich progress bar.

        Args:
            url: Media URL to download.
            output_dir: Directory to save downloaded file.
            audio_only: If True, extract audio only.
            format: Specific format to download.

        Returns:
            Path to downloaded file.
        """
        if not self.validate_url(url):
            raise YtDlpError(f"Invalid URL: {url}")

        output_dir = output_dir or Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get media info first
        try:
            info = self.get_media_info(url)
            console.print(Panel(
                f"[bold]{info.title}[/bold]\n"
                f"Uploader: {info.uploader or 'Unknown'}\n"
                f"Duration: {info.duration_seconds}s" if info.duration_seconds else "Duration: Unknown",
                title="📥 Downloading",
                style="blue",
            ))
        except YtDlpError as e:
            logger.warning(f"Could not fetch media info: {e}")

        # Build command with progress output
        cmd = [
            self._yt_dlp_path,
            "--newline",
            "--progress",
        ]

        output_template = str(output_dir / self.config.output_template)
        cmd.extend(["-o", output_template])

        if audio_only:
            audio_format = format or self.config.default_audio_format
            cmd.extend(["-x", "--audio-format", audio_format])

        if not audio_only and format:
            cmd.extend(["-f", f"bestvideo[ext={format}]+bestaudio/best"])

        cmd.extend(["--no-playlist", url])

        # Execute with progress display
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            console=console,
        )

        with progress:
            task_id = progress.add_task("Downloading...", total=None)
            
            import subprocess
            import sys

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            output_lines = []
            while True:
                line = process.stdout.readline() if process.stdout else ""
                if not line and process.poll() is not None:
                    break
                
                output_lines.append(line)
                
                # Parse progress from yt-dlp output
                if "%" in line and ("ETA" in line or "MiB" in line):
                    match = re.search(r"(\d+\.?\d*)%", line)
                    if match:
                        percent = float(match.group(1))
                        progress.update(task_id, completed=percent, total=100)

            process.wait()

            if process.returncode != 0:
                error_msg = "".join(output_lines[-5:])
                raise YtDlpError(f"Download failed: {error_msg}")

            progress.update(task_id, completed=100, total=100)

        # Find downloaded file
        downloaded_files = list(output_dir.glob("*"))
        if downloaded_files:
            latest = max(downloaded_files, key=lambda p: p.stat().st_mtime)
            return latest

        raise YtDlpError("Download completed but file not found")

    def download_playlist(
        self,
        url: str,
        output_dir: Optional[Path] = None,
        audio_only: bool = False,
        start_index: int = 1,
        end_index: Optional[int] = None,
    ) -> list[Path]:
        """Download an entire playlist.

        Args:
            url: Playlist URL.
            output_dir: Directory to save downloaded files.
            audio_only: If True, extract audio only.
            start_index: Starting item index (1-based).
            end_index: Ending item index (None for all).

        Returns:
            List of paths to downloaded files.
        """
        if not self.validate_url(url):
            raise YtDlpError(f"Invalid URL: {url}")

        output_dir = output_dir or Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            self._yt_dlp_path,
            "--yes-playlist",
            "--newline",
        ]

        if start_index > 1:
            cmd.extend(["--playlist-start", str(start_index)])
        if end_index:
            cmd.extend(["--playlist-end", str(end_index)])

        output_template = str(output_dir / "%(playlist)s" / self.config.output_template)
        cmd.extend(["-o", output_template])

        if audio_only:
            audio_format = self.config.default_audio_format
            cmd.extend(["-x", "--audio-format", audio_format])

        cmd.extend(["--prefer-free-formats", url])

        logger.info(f"Downloading playlist: {url}")

        result = run_command(cmd, timeout=None)

        if not result.success:
            raise YtDlpError(f"Playlist download failed: {result.stderr}")

        # Find all downloaded files
        downloaded = list(output_dir.rglob("*.*"))
        downloaded = [f for f in downloaded if f.is_file()]
        
        logger.info(f"Downloaded {len(downloaded)} files")
        return downloaded


def run_downloader(
    url: str,
    audio_only: bool = False,
    output_dir: Optional[Path] = None,
    format: Optional[str] = None,
    playlist: bool = False,
) -> None:
    """Run the downloader from CLI.

    Args:
        url: Media URL to download.
        audio_only: If True, download audio only.
        output_dir: Output directory.
        format: Desired format.
        playlist: If True, download as playlist.
    """
    try:
        downloader = MediaDownloader()
        
        if playlist:
            files = downloader.download_playlist(url, output_dir, audio_only)
            console.print(f"[green]✓ Downloaded {len(files)} files[/green]")
        else:
            file = downloader.download_with_progress(url, output_dir, audio_only, format)
            console.print(f"[green]✓ Downloaded: {file}[/green]")
            
    except YtDlpError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
