"""Configuration management module.

Handles loading, validating and saving user configuration.
"""

import tomllib
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ConfigModel(BaseModel):
    """Pydantic model for configuration validation."""

    max_connections: int = Field(default=8, ge=1, le=64)
    timeout: float = Field(default=30.0, ge=1.0)
    max_retries: int = Field(default=5, ge=0, le=10)
    rate_limit: Optional[str] = None
    download_dir: str = "."
    chunk_size: int = Field(default=1024 * 1024, ge=64 * 1024)
    min_segment_size: int = Field(default=64 * 1024, ge=1024)
    enable_http3: bool = False
    throttle_detection: bool = True


class Config:
    """Configuration manager for FastDL.

    Loads configuration from TOML file or uses defaults.
    Allows runtime overrides via CLI flags.
    """

    DEFAULT_CONFIG_NAME = "config.toml"
    CONFIG_DIR = ".config/fastdl"

    def __init__(self) -> None:
        """Initialize with default configuration."""
        self._config = ConfigModel()

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the path to the configuration file.

        Returns:
            Path to config.toml in user's home directory.
        """
        home = Path.home()
        config_dir = home / cls.CONFIG_DIR
        return config_dir / cls.DEFAULT_CONFIG_NAME

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file or create defaults.

        Returns:
            Config instance with loaded or default values.
        """
        config = cls()
        config_path = cls.get_config_path()

        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    data = tomllib.load(f)
                config._config = ConfigModel(**data)
            except (tomllib.TOMLDecodeError, ValueError) as e:
                print(f"[yellow]Warning: Invalid config file, using defaults. Error: {e}[/yellow]")

        return config

    def save(self) -> None:
        """Save current configuration to file."""
        config_path = self.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            import tomli_w

            tomli_w.dump(self._config.model_dump(), f)

    @property
    def max_connections(self) -> int:
        """Get maximum number of connections."""
        return self._config.max_connections

    @max_connections.setter
    def max_connections(self, value: int) -> None:
        """Set maximum number of connections."""
        self._config.max_connections = value

    @property
    def timeout(self) -> float:
        """Get timeout in seconds."""
        return self._config.timeout

    @property
    def max_retries(self) -> int:
        """Get maximum retry attempts."""
        return self._config.max_retries

    @property
    def rate_limit(self) -> Optional[str]:
        """Get rate limit string."""
        return self._config.rate_limit

    @rate_limit.setter
    def rate_limit(self, value: Optional[str]) -> None:
        """Set rate limit."""
        self._config.rate_limit = value

    @property
    def download_dir(self) -> str:
        """Get default download directory."""
        return self._config.download_dir

    @property
    def chunk_size(self) -> int:
        """Get default chunk size in bytes."""
        return self._config.chunk_size

    @property
    def min_segment_size(self) -> int:
        """Get minimum segment size in bytes."""
        return self._config.min_segment_size

    @property
    def enable_http3(self) -> bool:
        """Check if HTTP/3 is enabled."""
        return self._config.enable_http3

    @property
    def throttle_detection(self) -> bool:
        """Check if throttle detection is enabled."""
        return self._config.throttle_detection
