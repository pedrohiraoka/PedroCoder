"""Async HTTP client module.

Provides high-performance async HTTP client with connection pooling,
retry logic, and throttle detection.
"""

import asyncio
import httpx
from typing import Optional, AsyncGenerator, Callable
from dataclasses import dataclass
import random


@dataclass
class DownloadProgress:
    """Tracks download progress for a segment."""

    segment_id: int
    start_byte: int
    end_byte: int
    downloaded_bytes: int = 0
    speed_bytes_per_sec: float = 0.0
    retries: int = 0
    is_complete: bool = False
    is_failed: bool = False


class AsyncHTTPClient:
    """High-performance async HTTP client for downloads.

    Features:
    - Connection pooling
    - Exponential backoff retry
    - Throttle detection
    - Range request support
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 5,
        enable_http2: bool = True,
        enable_http3: bool = False,
    ) -> None:
        """Initialize the HTTP client.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts per request.
            enable_http2: Enable HTTP/2 support.
            enable_http3: Enable HTTP/3 (QUIC) support.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_http2 = enable_http2
        self.enable_http3 = enable_http3

        # HTTP limits configuration
        limits = httpx.Limits(
            max_keepalive_connections=100,
            max_connections=100,
            keepalive_expiry=30.0,
        )

        # Build transport with appropriate HTTP version support
        http2 = enable_http2
        # Note: HTTP/3 requires special setup, using http2 as fallback
        
        self._client: Optional[httpx.AsyncClient] = None
        self._limits = limits
        self._http2 = http2

    async def __aenter__(self) -> "AsyncHTTPClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=self._limits,
            http2=self._http2,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def download_range(
        self,
        url: str,
        start: int,
        end: int,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Download a byte range from a URL.

        Args:
            url: The URL to download from.
            start: Start byte position.
            end: End byte position (inclusive).
            progress_callback: Optional callback for progress updates.

        Yields:
            Chunks of downloaded data.

        Raises:
            httpx.HTTPError: If download fails after all retries.
        """
        retries = 0
        last_error: Optional[Exception] = None

        while retries <= self.max_retries:
            try:
                headers = {"Range": f"bytes={start}-{end}"}
                
                async with self._client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()
                    
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        if chunk:
                            yield chunk
                            if progress_callback:
                                progress_callback(len(chunk))
                    
                    return  # Success, exit retry loop

            except (httpx.ReadTimeout, httpx.ConnectError, httpx.NetworkError) as e:
                last_error = e
                retries += 1
                
                if retries <= self.max_retries:
                    # Exponential backoff with jitter
                    delay = min(2 ** retries + random.uniform(0, 1), 30)
                    await asyncio.sleep(delay)

        # All retries exhausted
        raise last_error or httpx.HTTPError("Max retries exceeded")

    async def get_file_size(self, url: str) -> int:
        """Get the size of a remote file.

        Args:
            url: The URL to check.

        Returns:
            File size in bytes.
        """
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        response = await self._client.head(url)
        response.raise_for_status()
        
        content_length = response.headers.get("Content-Length")
        return int(content_length) if content_length else 0

    def detect_throttling(
        self,
        current_speed: float,
        average_speed: float,
        threshold_ratio: float = 0.3,
    ) -> bool:
        """Detect if connection is being throttled.

        Args:
            current_speed: Current download speed in bytes/sec.
            average_speed: Average speed across all segments.
            threshold_ratio: Ratio below average to consider throttled.

        Returns:
            True if throttling is detected.
        """
        if average_speed == 0:
            return False
            
        ratio = current_speed / average_speed
        return ratio < threshold_ratio
