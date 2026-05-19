"""Tests for storage writer module."""

import pytest
import asyncio
from pathlib import Path
from pytest_mock import MockerFixture
from src.storage.writer import StorageWriter, IntegrityChecker, DownloadStateManager


class TestStorageWriter:
    """Test cases for StorageWriter class."""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create temporary directory for tests."""
        return tmp_path / "downloads"

    @pytest.fixture
    def writer(self, temp_dir: Path) -> StorageWriter:
        """Create storage writer instance."""
        temp_dir.mkdir(parents=True, exist_ok=True)
        dest_path = temp_dir / "testfile.bin"
        return StorageWriter(dest_path=dest_path, total_size=1024 * 1024)

    @pytest.mark.asyncio
    async def test_write_segment(
        self,
        writer: StorageWriter,
    ) -> None:
        """Test writing a segment to temporary storage."""
        segment_id = 0
        data = b"Hello, World!" * 100
        start_byte = 0

        await writer.write_segment(segment_id, data, start_byte)

        segment_path = writer.get_segment_path(segment_id)
        assert segment_path.exists()
        
        with open(segment_path, "rb") as f:
            content = f.read()
        
        assert content == data
        assert writer.written_segments[segment_id] is True

    @pytest.mark.asyncio
    async def test_merge_segments(
        self,
        writer: StorageWriter,
    ) -> None:
        """Test merging multiple segments into final file."""
        # Write multiple segments
        segments_data = [
            (0, b"Segment 0 data", 0),
            (1, b"Segment 1 data", 100),
            (2, b"Segment 2 data", 200),
        ]

        for segment_id, data, start_byte in segments_data:
            await writer.write_segment(segment_id, data, start_byte)

        # Merge segments
        await writer.merge_segments(total_segments=3)

        # Verify final file exists and contains all data
        assert writer.dest_path.exists()
        
        with open(writer.dest_path, "rb") as f:
            content = f.read()
        
        expected = b"".join([data for _, data, _ in segments_data])
        assert content == expected

    @pytest.mark.asyncio
    async def test_verify_complete(
        self,
        writer: StorageWriter,
    ) -> None:
        """Test verification of complete segments."""
        # Write some segments
        await writer.write_segment(0, b"data0", 0)
        await writer.write_segment(1, b"data1", 100)

        assert writer.verify_complete(total_segments=2) is True
        assert writer.verify_complete(total_segments=3) is False

    @pytest.mark.asyncio
    async def test_cleanup(
        self,
        writer: StorageWriter,
    ) -> None:
        """Test cleanup of temporary files."""
        # Write segments
        await writer.write_segment(0, b"data", 0)
        await writer.write_segment(1, b"data", 100)

        # Cleanup
        await writer.cleanup()

        # Verify temp directory is removed
        assert not writer.temp_dir.exists()


class TestIntegrityChecker:
    """Test cases for IntegrityChecker class."""

    @pytest.fixture
    def test_file(self, tmp_path: Path) -> Path:
        """Create test file with known content."""
        file_path = tmp_path / "test.bin"
        with open(file_path, "wb") as f:
            f.write(b"Test content for hashing")
        return file_path

    @pytest.mark.asyncio
    async def test_calculate_hash_sha256(
        self,
        test_file: Path,
    ) -> None:
        """Test SHA256 hash calculation."""
        checker = IntegrityChecker(algorithm="sha256")
        hash_value = await checker.calculate_hash(test_file)
        
        # Verify it's a valid hex string of correct length
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    @pytest.mark.asyncio
    async def test_calculate_hash_md5(
        self,
        test_file: Path,
    ) -> None:
        """Test MD5 hash calculation."""
        checker = IntegrityChecker(algorithm="md5")
        hash_value = await checker.calculate_hash(test_file)
        
        # Verify it's a valid hex string of correct length
        assert len(hash_value) == 32
        assert all(c in "0123456789abcdef" for c in hash_value)

    @pytest.mark.asyncio
    async def test_verify_success(
        self,
        test_file: Path,
    ) -> None:
        """Test successful hash verification."""
        checker = IntegrityChecker(algorithm="sha256")
        expected_hash = await checker.calculate_hash(test_file)
        
        result = await checker.verify(test_file, expected_hash)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_failure(
        self,
        test_file: Path,
    ) -> None:
        """Test failed hash verification."""
        checker = IntegrityChecker(algorithm="sha256")
        wrong_hash = "a" * 64  # Incorrect hash
        
        result = await checker.verify(test_file, wrong_hash)
        assert result is False

    def test_unsupported_algorithm(self) -> None:
        """Test initialization with unsupported algorithm."""
        with pytest.raises(ValueError):
            IntegrityChecker(algorithm="invalid_algo")


class TestDownloadStateManager:
    """Test cases for DownloadStateManager class."""

    @pytest.fixture
    def state_manager(self, tmp_path: Path) -> DownloadStateManager:
        """Create state manager instance."""
        dest_path = tmp_path / "download.bin"
        return DownloadStateManager(dest_path=dest_path)

    def test_save_and_load_state(
        self,
        state_manager: DownloadStateManager,
    ) -> None:
        """Test saving and loading download state."""
        url = "https://example.com/file.zip"
        total_size = 1048576
        etag = '"abc123"'
        completed_segments = [0, 1, 2]
        segment_ranges = {
            0: (0, 100),
            1: (101, 200),
            2: (201, 300),
        }

        state_manager.save_state(
            url=url,
            total_size=total_size,
            etag=etag,
            completed_segments=completed_segments,
            segment_ranges=segment_ranges,
        )

        # Verify state file exists
        assert state_manager.state_path.exists()

        # Load and verify
        state = state_manager.load_state()
        assert state is not None
        assert state["url"] == url
        assert state["total_size"] == total_size
        assert state["etag"] == etag
        assert state["completed_segments"] == completed_segments
        # segment_ranges are converted to tuples when loading
        assert list(state["segment_ranges"][0]) == [0, 100]

    def test_clear_state(
        self,
        state_manager: DownloadStateManager,
    ) -> None:
        """Test clearing saved state."""
        # Save state first
        state_manager.save_state(
            url="https://example.com/file.zip",
            total_size=1000,
            etag=None,
            completed_segments=[],
            segment_ranges={},
        )

        # Clear state
        state_manager.clear_state()

        # Verify state file is removed
        assert not state_manager.state_path.exists()

    def test_validate_state_success(
        self,
        state_manager: DownloadStateManager,
    ) -> None:
        """Test state validation when valid."""
        url = "https://example.com/file.zip"
        etag = '"same-etag"'

        state_manager.save_state(
            url=url,
            total_size=1000,
            etag=etag,
            completed_segments=[0],
            segment_ranges={0: (0, 100)},
        )

        result = state_manager.validate_state(url, etag)
        assert result is True

    def test_validate_state_url_mismatch(
        self,
        state_manager: DownloadStateManager,
    ) -> None:
        """Test state validation when URL changed."""
        state_manager.save_state(
            url="https://example.com/old.zip",
            total_size=1000,
            etag=None,
            completed_segments=[],
            segment_ranges={},
        )

        result = state_manager.validate_state("https://example.com/new.zip", None)
        assert result is False

    def test_validate_state_etag_mismatch(
        self,
        state_manager: DownloadStateManager,
    ) -> None:
        """Test state validation when ETag changed."""
        state_manager.save_state(
            url="https://example.com/file.zip",
            total_size=1000,
            etag='"old-etag"',
            completed_segments=[],
            segment_ranges={},
        )

        result = state_manager.validate_state(
            "https://example.com/file.zip",
            '"new-etag"',
        )
        assert result is False

    def test_load_nonexistent_state(
        self,
        state_manager: DownloadStateManager,
    ) -> None:
        """Test loading state when file doesn't exist."""
        result = state_manager.load_state()
        assert result is None
