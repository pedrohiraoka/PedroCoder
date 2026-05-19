"""Tests for network inspector module."""

import pytest
import httpx
from pytest_mock import MockerFixture
from src.network.inspector import NetworkInspector, FileInfo


class TestNetworkInspector:
    """Test cases for NetworkInspector class."""

    @pytest.fixture
    def inspector(self) -> NetworkInspector:
        """Create inspector instance."""
        return NetworkInspector(timeout=5.0)

    @pytest.mark.asyncio
    async def test_inspect_with_ranges_support(
        self,
        mocker: MockerFixture,
        inspector: NetworkInspector,
    ) -> None:
        """Test inspection when server supports range requests."""
        mock_response = mocker.Mock()
        mock_response.headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": "1048576",
            "Content-Type": "application/octet-stream",
            "ETag": '"abc123"',
            "Last-Modified": "Mon, 01 Jan 2026 00:00:00 GMT",
            "Content-Disposition": 'attachment; filename="test.zip"',
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.AsyncMock()
        mock_client.head = mocker.AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        file_info = await inspector.inspect("https://example.com/test.zip")

        assert file_info.url == "https://example.com/test.zip"
        assert file_info.size == 1048576
        assert file_info.supports_ranges is True
        assert file_info.content_type == "application/octet-stream"
        assert file_info.etag == '"abc123"'
        assert file_info.filename == "test.zip"

    @pytest.mark.asyncio
    async def test_inspect_without_ranges_support(
        self,
        mocker: MockerFixture,
        inspector: NetworkInspector,
    ) -> None:
        """Test inspection when server doesn't support range requests."""
        mock_response = mocker.Mock()
        mock_response.headers = {
            "Accept-Ranges": "none",
            "Content-Length": "1048576",
            "Content-Type": "text/html",
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.AsyncMock()
        mock_client.head = mocker.AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        file_info = await inspector.inspect("https://example.com/page.html")

        assert file_info.supports_ranges is False
        assert file_info.content_type == "text/html"

    @pytest.mark.asyncio
    async def test_extract_filename_from_content_disposition(
        self,
        inspector: NetworkInspector,
    ) -> None:
        """Test filename extraction from Content-Disposition header."""
        # Standard format
        filename = inspector._extract_filename('attachment; filename="test.zip"')
        assert filename == "test.zip"

        # Without quotes
        filename = inspector._extract_filename("attachment; filename=test.zip")
        assert filename == "test.zip"

        # RFC 5987 encoding
        filename = inspector._extract_filename(
            "attachment; filename*=utf-8''t%C3%AAst.zip"
        )
        assert filename == "t%C3%AAst.zip"

        # No filename
        filename = inspector._extract_filename("attachment")
        assert filename is None

        # Empty header
        filename = inspector._extract_filename("")
        assert filename is None

    @pytest.mark.asyncio
    async def test_validate_resume_support_true(
        self,
        mocker: MockerFixture,
        inspector: NetworkInspector,
    ) -> None:
        """Test resume validation when supported."""
        mock_response = mocker.Mock()
        mock_response.headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": "1000",
            "ETag": '"same-etag"',
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.AsyncMock()
        mock_client.head = mocker.AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        result = await inspector.validate_resume_support(
            "https://example.com/file.bin",
            etag='"same-etag"',
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_resume_support_etag_mismatch(
        self,
        mocker: MockerFixture,
        inspector: NetworkInspector,
    ) -> None:
        """Test resume validation when ETag changed."""
        mock_response = mocker.Mock()
        mock_response.headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": "1000",
            "ETag": '"different-etag"',
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.AsyncMock()
        mock_client.head = mocker.AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        result = await inspector.validate_resume_support(
            "https://example.com/file.bin",
            etag='"old-etag"',
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_resume_support_no_ranges(
        self,
        mocker: MockerFixture,
        inspector: NetworkInspector,
    ) -> None:
        """Test resume validation when ranges not supported."""
        mock_response = mocker.Mock()
        mock_response.headers = {
            "Accept-Ranges": "none",
            "Content-Length": "1000",
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.AsyncMock()
        mock_client.head = mocker.AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        result = await inspector.validate_resume_support("https://example.com/file.bin")

        assert result is False

    @pytest.mark.asyncio
    async def test_inspect_http_error(
        self,
        mocker: MockerFixture,
        inspector: NetworkInspector,
    ) -> None:
        """Test inspection when HTTP error occurs."""
        mock_client = mocker.AsyncMock()
        mock_client.head = mocker.AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=mocker.Mock(),
                response=mocker.Mock(),
            )
        )
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        with pytest.raises(httpx.HTTPStatusError):
            await inspector.inspect("https://example.com/notfound.zip")
