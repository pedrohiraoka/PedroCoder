"""Main download manager module.

Orchestrates the parallel download process with segment management,
progress tracking, and user interface updates.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from rich.console import Console
from rich.live import Live
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)
from rich.table import Table
from rich.panel import Panel

from src.utils.config import Config
from src.network.client import AsyncHTTPClient
from src.network.inspector import NetworkInspector, FileInfo
from src.storage.writer import StorageWriter, DownloadStateManager


@dataclass
class SegmentTask:
    """Represents a download segment task."""

    segment_id: int
    start_byte: int
    end_byte: int
    downloaded_bytes: int = 0
    is_complete: bool = False
    is_failed: bool = False
    retries: int = 0
    speed: float = 0.0


@dataclass
class DownloadStats:
    """Real-time download statistics."""

    total_size: int = 0
    downloaded_bytes: int = 0
    start_time: float = 0.0
    current_speed: float = 0.0
    average_speed: float = 0.0
    peak_speed: float = 0.0
    eta_seconds: float = 0.0
    active_connections: int = 0
    completed_segments: int = 0
    total_segments: int = 0
    errors: List[str] = field(default_factory=list)


class DownloadManager:
    """Main orchestrator for parallel downloads.

    Manages segment distribution, concurrent downloads, progress tracking,
    and file assembly.
    """

    def __init__(self, config: Config, quiet: bool = False) -> None:
        """Initialize the download manager.

        Args:
            config: Configuration object.
            quiet: If True, suppress UI output.
        """
        self.config = config
        self.quiet = quiet
        self.console = Console() if not quiet else None
        
        self.stats = DownloadStats()
        self.segments: List[SegmentTask] = []
        self._cancel_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused by default
        
        self._inspector = NetworkInspector(timeout=config.timeout)
        self._state_manager: Optional[DownloadStateManager] = None
        self._storage_writer: Optional[StorageWriter] = None

    def _calculate_segments(
        self,
        total_size: int,
        num_segments: int,
        min_segment_size: int,
    ) -> List[tuple]:
        """Calculate byte ranges for segments.

        Args:
            total_size: Total file size in bytes.
            num_segments: Desired number of segments.
            min_segment_size: Minimum segment size in bytes.

        Returns:
            List of (start, end) tuples for each segment.
        """
        # Adjust segment count if file is too small
        if total_size < num_segments * min_segment_size:
            num_segments = max(1, total_size // min_segment_size)
        
        if num_segments == 0:
            return [(0, total_size - 1)] if total_size > 0 else []
        
        segments = []
        chunk_size = total_size // num_segments
        
        for i in range(num_segments):
            start = i * chunk_size
            if i == num_segments - 1:
                # Last segment gets remaining bytes
                end = total_size - 1
            else:
                end = start + chunk_size - 1
            
            segments.append((start, end))
        
        return segments

    async def _download_segment(
        self,
        client: AsyncHTTPClient,
        url: str,
        segment: SegmentTask,
        writer: StorageWriter,
        semaphore: asyncio.Semaphore,
    ) -> None:
        """Download a single segment.

        Args:
            client: HTTP client instance.
            url: Download URL.
            segment: Segment task to download.
            writer: Storage writer instance.
            semaphore: Concurrency limiter.
        """
        async with semaphore:
            while not self._cancel_event.is_set():
                # Wait if paused
                await self._pause_event.wait()
                
                if self._cancel_event.is_set():
                    break
                
                try:
                    start_pos = segment.start_byte + segment.downloaded_bytes
                    end_pos = segment.end_byte
                    
                    buffer = bytearray()
                    
                    async for chunk in client.download_range(
                        url=url,
                        start=start_pos,
                        end=end_pos,
                    ):
                        if self._cancel_event.is_set():
                            break
                        
                        buffer.extend(chunk)
                        segment.downloaded_bytes += len(chunk)
                        
                        # Update stats
                        self.stats.downloaded_bytes += len(chunk)
                    
                    if buffer and not self._cancel_event.is_set():
                        # Write segment to storage
                        await writer.write_segment(
                            segment_id=segment.segment_id,
                            data=bytes(buffer),
                            start_byte=segment.start_byte,
                        )
                        segment.is_complete = True
                        self.stats.completed_segments += 1
                    
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    segment.retries += 1
                    self.stats.errors.append(f"Segment {segment.segment_id}: {e}")
                    
                    if segment.retries >= self.config.max_retries:
                        segment.is_failed = True
                        break
                    
                    # Exponential backoff
                    delay = min(2 ** segment.retries, 30)
                    await asyncio.sleep(delay)

    def _create_progress_display(self) -> Table:
        """Create rich table for progress display.

        Returns:
            Rich Table with download metrics.
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold white")
        
        # Calculate percentage
        if self.stats.total_size > 0:
            percentage = (self.stats.downloaded_bytes / self.stats.total_size) * 100
        else:
            percentage = 0.0
        
        # Format speeds
        def format_speed(speed: float) -> str:
            if speed >= 1_000_000:
                return f"{speed / 1_000_000:.1f} MB/s"
            elif speed >= 1_000:
                return f"{speed / 1_000:.1f} KB/s"
            else:
                return f"{speed:.0f} B/s"
        
        table.add_row("Progress:", f"{percentage:.1f}%")
        table.add_row("Downloaded:", f"{self.stats.downloaded_bytes:,} / {self.stats.total_size:,} bytes")
        table.add_row("Speed (Current):", format_speed(self.stats.current_speed))
        table.add_row("Speed (Average):", format_speed(self.stats.average_speed))
        table.add_row("Speed (Peak):", format_speed(self.stats.peak_speed))
        table.add_row("ETA:", f"{self.stats.eta_seconds:.0f}s")
        table.add_row("Connections:", f"{self.stats.active_connections}/{len(self.segments)}")
        table.add_row("Completed:", f"{self.stats.completed_segments}/{self.stats.total_segments}")
        
        if self.stats.errors:
            table.add_row("Errors:", f"[red]{len(self.stats.errors)}[/red]")
        
        return table

    async def download(
        self,
        url: str,
        dest_path: Optional[Path] = None,
        resume: bool = False,
    ) -> None:
        """Start the download process.

        Args:
            url: URL to download from.
            dest_path: Destination file path (optional).
            resume: If True, attempt to resume interrupted download.
        """
        # Inspect the URL
        if not self.quiet:
            self.console.print("[cyan]Inspecting URL...[/cyan]")
        
        file_info = await self._inspector.inspect(url)
        
        if not file_info.supports_ranges:
            if not self.quiet:
                self.console.print(
                    "[yellow]Warning: Server does not support range requests. "
                    "Falling back to single connection.[/yellow]"
                )
        
        # Determine destination path
        if not dest_path:
            filename = file_info.filename or url.split("/")[-1].split("?")[0]
            dest_path = Path(filename)
        
        dest_path = Path(dest_path).resolve()
        
        # Initialize state manager
        self._state_manager = DownloadStateManager(dest_path)
        
        # Check for resume
        completed_segments: List[int] = []
        if resume and self._state_manager.validate_state(url, file_info.etag):
            if not self.quiet:
                self.console.print("[green]Resuming download...[/green]")
            
            state = self._state_manager.load_state()
            if state:
                completed_segments = state.get("completed_segments", [])
        else:
            if not self.quiet:
                self.console.print(f"[cyan]Starting new download:[/cyan] {dest_path.name}")
        
        # Calculate segments
        num_segments = (
            self.config.max_connections
            if file_info.supports_ranges
            else 1
        )
        
        segment_ranges = self._calculate_segments(
            total_size=file_info.size,
            num_segments=num_segments,
            min_segment_size=self.config.min_segment_size,
        )
        
        # Create segment tasks
        self.segments = []
        for i, (start, end) in enumerate(segment_ranges):
            if i in completed_segments:
                continue  # Skip already completed segments
            
            self.segments.append(
                SegmentTask(
                    segment_id=i,
                    start_byte=start,
                    end_byte=end,
                )
            )
        
        self.stats.total_size = file_info.size
        self.stats.total_segments = len(self.segments) + len(completed_segments)
        self.stats.completed_segments = len(completed_segments)
        
        # Initialize storage writer
        self._storage_writer = StorageWriter(
            dest_path=dest_path,
            total_size=file_info.size,
            chunk_size=self.config.chunk_size,
        )
        
        # Start download with progress display
        self.stats.start_time = time.time()
        
        if self.quiet:
            await self._run_download(url, file_info.etag)
        else:
            with Live(
                self._create_progress_display(),
                refresh_per_second=5,
                console=self.console,
            ) as live:
                await self._run_download(url, file_info.etag)
                live.update(self._create_progress_display())
        
        # Check for cancellation
        if self._cancel_event.is_set():
            # Save state for resume
            if self._state_manager:
                completed = [s.segment_id for s in self.segments if s.is_complete]
                self._state_manager.save_state(
                    url=url,
                    total_size=file_info.size,
                    etag=file_info.etag,
                    completed_segments=completed,
                    segment_ranges={s.segment_id: (s.start_byte, s.end_byte) for s in self.segments},
                )
            return
        
        # Merge segments
        if not self.quiet:
            self.console.print("[cyan]Merging segments...[/cyan]")
        
        await self._storage_writer.merge_segments(self.stats.total_segments)
        
        # Cleanup
        await self._storage_writer.cleanup()
        if self._state_manager:
            self._state_manager.clear_state()
        
        if not self.quiet:
            elapsed = time.time() - self.stats.start_time
            self.console.print(
                f"\n[bold green]✓ Download complete![/bold green]\n"
                f"File: {dest_path}\n"
                f"Size: {file_info.size:,} bytes\n"
                f"Time: {elapsed:.1f}s\n"
                f"Avg Speed: {self.stats.average_speed / 1_000_000:.2f} MB/s"
            )

    async def _run_download(self, url: str, etag: Optional[str]) -> None:
        """Run the actual download process.

        Args:
            url: Download URL.
            etag: Server ETag for validation.
        """
        semaphore = asyncio.Semaphore(self.config.max_connections)
        
        async with AsyncHTTPClient(
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        ) as client:
            # Create tasks for all segments
            tasks = [
                asyncio.create_task(
                    self._download_segment(
                        client=client,
                        url=url,
                        segment=segment,
                        writer=self._storage_writer,  # type: ignore
                        semaphore=semaphore,
                    )
                )
                for segment in self.segments
            ]
            
            # Monitor progress while tasks run
            last_downloaded = 0
            monitor_interval = 0.2  # seconds
            
            while not all(task.done() for task in tasks):
                # Update statistics
                now = time.time()
                elapsed = now - self.stats.start_time
                
                # Calculate speeds
                delta = self.stats.downloaded_bytes - last_downloaded
                self.stats.current_speed = delta / monitor_interval
                self.stats.average_speed = self.stats.downloaded_bytes / elapsed if elapsed > 0 else 0
                self.stats.peak_speed = max(self.stats.peak_speed, self.stats.current_speed)
                
                # Calculate ETA
                remaining = self.stats.total_size - self.stats.downloaded_bytes
                if self.stats.average_speed > 0:
                    self.stats.eta_seconds = remaining / self.stats.average_speed
                else:
                    self.stats.eta_seconds = 0
                
                # Count active connections
                self.stats.active_connections = sum(
                    1 for s in self.segments
                    if not s.is_complete and not s.is_failed
                )
                
                last_downloaded = self.stats.downloaded_bytes
                
                # Wait before next update
                await asyncio.sleep(monitor_interval)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

    def pause(self) -> None:
        """Pause the download."""
        self._pause_event.clear()
        if self.console:
            self.console.print("[yellow]Pausing download...[/yellow]")

    def resume(self) -> None:
        """Resume a paused download."""
        self._pause_event.set()
        if self.console:
            self.console.print("[green]Resuming download...[/green]")

    def cancel(self) -> None:
        """Cancel the download."""
        self._cancel_event.set()
        if self.console:
            self.console.print("[yellow]Cancelling download...[/yellow]")
