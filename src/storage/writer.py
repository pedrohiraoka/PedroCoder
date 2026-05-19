"""Storage management module.

Handles file writing, merging segments, and integrity verification.
"""

import asyncio
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
import json


class StorageWriter:
    """Manages file writing operations for downloads.

    Features:
    - Sequential writes to avoid lock contention
    - Buffer management for memory efficiency
    - Atomic file operations
    - Temporary segment storage
    """

    def __init__(
        self,
        dest_path: Path,
        total_size: int,
        chunk_size: int = 1024 * 1024,
    ) -> None:
        """Initialize the storage writer.

        Args:
            dest_path: Final destination file path.
            total_size: Total expected file size in bytes.
            chunk_size: Size of write buffers.
        """
        self.dest_path = Path(dest_path)
        self.total_size = total_size
        self.chunk_size = chunk_size
        
        # Temporary files for segments
        self.temp_dir = dest_path.parent / f".{dest_path.name}.parts"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Track written segments
        self.written_segments: Dict[int, bool] = {}
        self._lock = asyncio.Lock()

    def get_segment_path(self, segment_id: int) -> Path:
        """Get the temporary path for a segment.

        Args:
            segment_id: The segment identifier.

        Returns:
            Path to the segment's temporary file.
        """
        return self.temp_dir / f"segment_{segment_id}.part"

    async def write_segment(
        self,
        segment_id: int,
        data: bytes,
        start_byte: int,
    ) -> None:
        """Write a segment to temporary storage.

        Args:
            segment_id: Segment identifier.
            data: The binary data to write.
            start_byte: Starting byte position in final file.
        """
        segment_path = self.get_segment_path(segment_id)
        
        async with self._lock:
            # Write segment to temp file
            with open(segment_path, "wb") as f:
                f.write(data)
            
            self.written_segments[segment_id] = True

    async def merge_segments(self, total_segments: int) -> None:
        """Merge all segments into the final file.

        Args:
            total_segments: Total number of expected segments.
        """
        # Open final file for writing
        with open(self.dest_path, "wb") as final_file:
            for segment_id in range(total_segments):
                segment_path = self.get_segment_path(segment_id)
                
                if not segment_path.exists():
                    raise FileNotFoundError(
                        f"Segment {segment_id} not found at {segment_path}"
                    )
                
                # Read and write segment
                with open(segment_path, "rb") as segment_file:
                    while chunk := segment_file.read(self.chunk_size):
                        final_file.write(chunk)
                
                # Remove temp segment
                segment_path.unlink()

    async def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir.exists():
            for file in self.temp_dir.glob("*.part"):
                file.unlink()
            self.temp_dir.rmdir()

    def verify_complete(self, total_segments: int) -> bool:
        """Verify all segments are written.

        Args:
            total_segments: Expected number of segments.

        Returns:
            True if all segments are present.
        """
        return len(self.written_segments) == total_segments


class IntegrityChecker:
    """Verifies file integrity using hashes.

    Supports MD5, SHA1, SHA256 checksums.
    """

    def __init__(self, algorithm: str = "sha256") -> None:
        """Initialize the checker.

        Args:
            algorithm: Hash algorithm to use.
        """
        self.algorithm = algorithm.lower()
        if self.algorithm not in ("md5", "sha1", "sha256", "sha512"):
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    async def calculate_hash(self, file_path: Path) -> str:
        """Calculate hash of a file.

        Args:
            file_path: Path to the file.

        Returns:
            Hex digest of the file hash.
        """
        hash_func = getattr(hashlib, self.algorithm)()
        
        loop = asyncio.get_event_loop()
        
        def _read_and_hash() -> str:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        
        return await loop.run_in_executor(None, _read_and_hash)

    async def verify(
        self,
        file_path: Path,
        expected_hash: str,
        algorithm: Optional[str] = None,
    ) -> bool:
        """Verify file against expected hash.

        Args:
            file_path: Path to the file.
            expected_hash: Expected hash value.
            algorithm: Override algorithm if needed.

        Returns:
            True if hash matches.
        """
        algo = algorithm or self.algorithm
        checker = IntegrityChecker(algo)
        actual_hash = await checker.calculate_hash(file_path)
        
        return actual_hash.lower() == expected_hash.lower()


class DownloadStateManager:
    """Manages download state for resume functionality.

    Persists download progress to allow resuming interrupted downloads.
    """

    STATE_FILE_SUFFIX = ".download_state.json"

    def __init__(self, dest_path: Path) -> None:
        """Initialize state manager.

        Args:
            dest_path: Path to the downloaded file.
        """
        self.dest_path = Path(dest_path)
        self.state_path = Path(str(dest_path) + self.STATE_FILE_SUFFIX)

    def save_state(
        self,
        url: str,
        total_size: int,
        etag: Optional[str],
        completed_segments: List[int],
        segment_ranges: Dict[int, tuple],
    ) -> None:
        """Save current download state.

        Args:
            url: Download URL.
            total_size: Total file size.
            etag: Server ETag.
            completed_segments: List of completed segment IDs.
            segment_ranges: Mapping of segment ID to (start, end) tuples.
        """
        state = {
            "url": url,
            "total_size": total_size,
            "etag": etag,
            "completed_segments": completed_segments,
            "segment_ranges": {str(k): list(v) for k, v in segment_ranges.items()},
            "timestamp": str(asyncio.get_event_loop().time()),
        }

        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load saved download state.

        Returns:
            State dictionary or None if no state exists.
        """
        if not self.state_path.exists():
            return None

        try:
            with open(self.state_path, "r") as f:
                state = json.load(f)
            
            # Convert string keys back to integers
            if "segment_ranges" in state:
                state["segment_ranges"] = {
                    int(k): tuple(v) for k, v in state["segment_ranges"].items()
                }
            
            return state
        except (json.JSONDecodeError, KeyError):
            return None

    def clear_state(self) -> None:
        """Clear saved state after successful download."""
        if self.state_path.exists():
            self.state_path.unlink()

    def validate_state(self, url: str, etag: Optional[str]) -> bool:
        """Validate if saved state is still valid.

        Args:
            url: Current download URL.
            etag: Current server ETag.

        Returns:
            True if state is valid for resume.
        """
        state = self.load_state()
        
        if not state:
            return False
        
        # Check URL matches
        if state.get("url") != url:
            return False
        
        # Check ETag if available
        if etag and state.get("etag") and state.get("etag") != etag:
            return False
        
        return True
