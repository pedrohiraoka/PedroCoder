"""Tests for configuration module."""

import pytest
import tomli_w
import tomllib
from pathlib import Path
from pydantic import ValidationError
from src.utils.config import Config, ConfigModel


class TestConfigModel:
    """Test cases for ConfigModel Pydantic model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ConfigModel()
        
        assert config.max_connections == 8
        assert config.timeout == 30.0
        assert config.max_retries == 5
        assert config.rate_limit is None
        assert config.download_dir == "."
        assert config.chunk_size == 1024 * 1024
        assert config.min_segment_size == 64 * 1024
        assert config.enable_http3 is False
        assert config.throttle_detection is True

    def test_valid_custom_values(self) -> None:
        """Test configuration with custom valid values."""
        config = ConfigModel(
            max_connections=16,
            timeout=60.0,
            max_retries=3,
            rate_limit="10M",
            download_dir="/downloads",
        )
        
        assert config.max_connections == 16
        assert config.timeout == 60.0
        assert config.max_retries == 3
        assert config.rate_limit == "10M"
        assert config.download_dir == "/downloads"

    def test_invalid_max_connections_too_low(self) -> None:
        """Test validation fails for max_connections below minimum."""
        with pytest.raises(ValidationError):
            ConfigModel(max_connections=0)

    def test_invalid_max_connections_too_high(self) -> None:
        """Test validation fails for max_connections above maximum."""
        with pytest.raises(ValidationError):
            ConfigModel(max_connections=100)

    def test_invalid_timeout_too_low(self) -> None:
        """Test validation fails for timeout below minimum."""
        with pytest.raises(ValidationError):
            ConfigModel(timeout=0.5)

    def test_invalid_max_retries(self) -> None:
        """Test validation fails for invalid max_retries."""
        with pytest.raises(ValidationError):
            ConfigModel(max_retries=-1)

    def test_invalid_chunk_size_too_small(self) -> None:
        """Test validation fails for chunk_size below minimum."""
        with pytest.raises(ValidationError):
            ConfigModel(chunk_size=1024)


class TestConfig:
    """Test cases for Config class."""

    def test_get_config_path(self) -> None:
        """Test configuration path generation."""
        config_path = Config.get_config_path()
        
        # Should be in home directory
        assert config_path.parent.name == "fastdl"
        assert config_path.name == "config.toml"

    def test_load_default_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading configuration when no file exists."""
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        config = Config.load()
        
        # Should have default values
        assert config.max_connections == 8
        assert config.timeout == 30.0

    def test_load_from_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading configuration from TOML file."""
        # Setup mock home directory
        config_dir = tmp_path / ".config" / "fastdl"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        
        # Write test config
        config_data = {
            "max_connections": 16,
            "timeout": 45.0,
            "download_dir": "/custom/downloads",
        }
        
        with open(config_file, "wb") as f:
            import tomli_w
            tomli_w.dump(config_data, f)
        
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Load config
        config = Config.load()
        
        assert config.max_connections == 16
        assert config.timeout == 45.0
        assert config.download_dir == "/custom/downloads"

    def test_load_invalid_toml(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        """Test loading configuration with invalid TOML."""
        # Setup mock home directory
        config_dir = tmp_path / ".config" / "fastdl"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        
        # Write invalid TOML
        with open(config_file, "w") as f:
            f.write("invalid toml {{{")
        
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Load config (should use defaults and print warning)
        config = Config.load()
        
        # Should have default values
        assert config.max_connections == 8
        
        # Check warning was printed
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "Invalid config" in captured.out

    def test_setters(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configuration setters."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        config = Config.load()
        
        # Test setters
        config.max_connections = 32
        assert config.max_connections == 32
        
        config.rate_limit = "5M"
        assert config.rate_limit == "5M"

    def test_properties(self) -> None:
        """Test configuration property accessors."""
        config = Config()
        
        assert isinstance(config.timeout, float)
        assert isinstance(config.max_retries, int)
        assert isinstance(config.download_dir, str)
        assert isinstance(config.chunk_size, int)
        assert isinstance(config.min_segment_size, int)
        assert isinstance(config.enable_http3, bool)
        assert isinstance(config.throttle_detection, bool)
