"""Configuration management for LTA.

Handles loading, validation, and merging of configuration from
YAML files with pydantic schema validation.
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


class NetworkConfig(BaseModel):
    """Network-related configuration settings."""

    ip_backends: list[str] = Field(
        default_factory=lambda: [
            "https://api.ipify.org",
            "https://ifconfig.me/ip",
            "https://icanhazip.com",
        ],
        description="List of IP lookup backends with fallback order",
    )
    timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        description="HTTP request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for network requests",
    )


class DownloaderConfig(BaseModel):
    """Downloader (yt-dlp) configuration settings."""

    default_audio_format: str = Field(
        default="mp3",
        description="Default audio format for extraction",
    )
    default_video_format: str = Field(
        default="mp4",
        description="Default video format",
    )
    output_template: str = Field(
        default="%(title)s.%(ext)s",
        description="Output filename template",
    )
    prefer_free_formats: bool = Field(
        default=False,
        description="Prefer free formats when available",
    )
    rate_limit: Optional[str] = Field(
        default=None,
        description="Download rate limit (e.g., '50K', '4.2M')",
    )


class SystemConfig(BaseModel):
    """System monitoring and administration configuration."""

    refresh_interval_ms: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="UI refresh interval in milliseconds",
    )
    log_lines_default: int = Field(
        default=100,
        ge=10,
        le=10000,
        description="Default number of log lines to display",
    )
    package_manager_timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Timeout for package manager operations in seconds",
    )


class UIConfig(BaseModel):
    """User interface configuration settings."""

    use_colors: bool = Field(
        default=True,
        description="Enable colored output",
    )
    use_icons: bool = Field(
        default=True,
        description="Enable Unicode icons in output",
    )
    width_threshold: int = Field(
        default=80,
        ge=40,
        description="Minimum terminal width for full UI",
    )
    progress_bar_width: int = Field(
        default=40,
        ge=20,
        le=100,
        description="Width of progress bars",
    )


class Config(BaseModel):
    """Main configuration model for LTA."""

    network: NetworkConfig = Field(default_factory=NetworkConfig)
    downloader: DownloaderConfig = Field(default_factory=DownloaderConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging",
    )
    config_version: str = Field(
        default="1.0",
        description="Configuration schema version",
    )


class ConfigManager:
    """Manages loading and accessing LTA configuration.

    Handles merging of default config with user overrides,
    environment variables, and CLI arguments.
    """

    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "defaults.yaml"
    USER_CONFIG_PATH = Path.home() / ".config" / "lta" / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Optional custom path to configuration file.
        """
        self._config: Optional[Config] = None
        self._config_path = config_path
        self._logger = None  # Will be set after logger is available

    def load(self) -> Config:
        """Load and merge configuration from all sources.

        Returns:
            Merged and validated configuration object.

        Raises:
            ConfigurationError: If configuration is invalid or unreadable.
        """
        if self._config is not None:
            return self._config

        config_data = self._load_defaults()
        user_config = self._load_user_config()

        if user_config:
            config_data = self._merge_configs(config_data, user_config)

        env_overrides = self._load_env_overrides()
        if env_overrides:
            config_data = self._merge_configs(config_data, env_overrides)

        try:
            self._config = Config(**config_data)
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e

        return self._config

    def _load_defaults(self) -> dict[str, Any]:
        """Load default configuration from bundled file.

        Returns:
            Dictionary of default configuration values.
        """
        if self._config_path and self._config_path.exists():
            return self._parse_yaml_file(self._config_path)

        if self.DEFAULT_CONFIG_PATH.exists():
            return self._parse_yaml_file(self.DEFAULT_CONFIG_PATH)

        return {}

    def _load_user_config(self) -> Optional[dict[str, Any]]:
        """Load user-specific configuration override.

        Returns:
            Dictionary of user configuration or None if not found.
        """
        if self.USER_CONFIG_PATH.exists():
            return self._parse_yaml_file(self.USER_CONFIG_PATH)
        return None

    def _load_env_overrides(self) -> dict[str, Any]:
        """Load configuration overrides from environment variables.

        Environment variables should be prefixed with LTA_ and use
        double underscore for nested keys (e.g., LTA_NETWORK__TIMEOUT_SECONDS).

        Returns:
            Dictionary of environment-based overrides.
        """
        overrides: dict[str, Any] = {}
        prefix = "LTA_"

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            nested_key = key[len(prefix) :].lower().replace("__", ".")
            parts = nested_key.split(".")

            current = overrides
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            final_key = parts[-1]
            current[final_key] = self._parse_env_value(value)

        return overrides

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable string to appropriate type.

        Args:
            value: String value from environment.

        Returns:
            Parsed value (bool, int, float, or str).
        """
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        return value

    def _parse_yaml_file(self, path: Path) -> dict[str, Any]:
        """Parse a YAML configuration file.

        Args:
            path: Path to YAML file.

        Returns:
            Parsed configuration dictionary.

        Raises:
            ConfigurationError: If file cannot be parsed.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse {path}: {e}") from e
        except OSError as e:
            raise ConfigurationError(f"Failed to read {path}: {e}") from e

    def _merge_configs(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two configuration dictionaries.

        Args:
            base: Base configuration dictionary.
            override: Override configuration dictionary.

        Returns:
            Merged configuration dictionary.
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    @property
    def config(self) -> Config:
        """Get the loaded configuration.

        Returns:
            Current configuration object.

        Raises:
            ConfigurationError: If configuration has not been loaded.
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded. Call load() first.")
        return self._config


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""

    pass


def get_config(config_path: Optional[Path] = None) -> Config:
    """Convenience function to get configuration instance.

    Args:
        config_path: Optional custom configuration file path.

    Returns:
        Loaded configuration object.
    """
    manager = ConfigManager(config_path)
    return manager.load()
