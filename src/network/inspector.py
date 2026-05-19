"""Network inspection module.

Handles HTTP header analysis, range support detection, and file metadata extraction.
"""

import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Information about a remote file."""

    url: str
    size: int
    supports_ranges: bool
    content_type: str
    etag: Optional[str] = None
    filename: Optional[str] = None
    last_modified: Optional[str] = None


class NetworkInspector:
    """Inspects HTTP servers for download capabilities.

    Detects support for range requests, extracts file metadata,
    and validates server capabilities before downloading.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize inspector with timeout.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout

    async def inspect(self, url: str) -> FileInfo:
        """Inspect a URL to gather file information.

        Args:
            url: The URL to inspect.

        Returns:
            FileInfo object with metadata.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.head(url, follow_redirects=True)
            response.raise_for_status()

            headers = response.headers

            # Check for range support
            accept_ranges = headers.get("Accept-Ranges", "").lower()
            supports_ranges = accept_ranges == "bytes"

            # Get content length
            content_length = headers.get("Content-Length")
            size = int(content_length) if content_length else 0

            # Extract other metadata
            etag = headers.get("ETag")
            content_type = headers.get("Content-Type", "application/octet-stream")
            last_modified = headers.get("Last-Modified")

            # Try to extract filename from Content-Disposition
            filename = self._extract_filename(headers.get("Content-Disposition", ""))

            return FileInfo(
                url=url,
                size=size,
                supports_ranges=supports_ranges,
                content_type=content_type,
                etag=etag,
                filename=filename,
                last_modified=last_modified,
            )

    @staticmethod
    def _extract_filename(content_disposition: str) -> Optional[str]:
        """Extract filename from Content-Disposition header.

        Args:
            content_disposition: The Content-Disposition header value.

        Returns:
            Filename if found, None otherwise.
        """
        if not content_disposition:
            return None

        # Look for filename= or filename*=
        for part in content_disposition.split(";"):
            part = part.strip()
            if part.startswith("filename="):
                return part.split("=", 1)[1].strip('"\'')
            elif part.startswith("filename*="):
                # Handle RFC 5987 encoding
                value = part.split("=", 1)[1].strip('"\'')
                if "'" in value:
                    # Format: utf-8''filename.txt
                    parts = value.split("'", 2)
                    if len(parts) == 3:
                        return parts[2]
                return value

        return None

    async def validate_resume_support(self, url: str, etag: Optional[str] = None) -> bool:
        """Validate if resume is supported and safe.

        Args:
            url: The URL to check.
            etag: Expected ETag from previous download.

        Returns:
            True if resume is safe, False otherwise.
        """
        try:
            info = await self.inspect(url)

            if not info.supports_ranges:
                return False

            # If we have an ETag, verify it matches
            if etag and info.etag and info.etag != etag:
                return False

            return True
        except httpx.HTTPError:
            return False
