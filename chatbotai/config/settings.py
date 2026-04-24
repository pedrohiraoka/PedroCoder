"""
Configuration management for ChatBotAI.

Provides configuration loading from YAML and environment variables.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama AI engine."""

    model_name: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    timeout: int = 60
    temperature: float = 0.7
    top_p: float = 0.9


@dataclass
class MemoryConfig:
    """Configuration for memory backends."""

    volatile_enabled: bool = True
    persistent_enabled: bool = False
    storage_path: str = "./chatbot_memory"
    max_entries: int = 1000


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = "INFO"
    format: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file: Optional[str] = None


@dataclass
class ChatBotConfig:
    """Main configuration for ChatBotAI."""

    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    system_prompt: str = (
        "You are a helpful, friendly, and knowledgeable assistant."
    )
    max_context_messages: int = 10


class ConfigLoader:
    """
    Loads and manages configuration from various sources.

    Supports YAML files, environment variables, and programmatic
    configuration with proper precedence.
    """

    def __init__(self) -> None:
        """Initialize the configuration loader."""
        self._config: Dict[str, Any] = {}
        self._config_paths: List[Path] = []

    def load_from_yaml(self, config_path: str) -> "ConfigLoader":
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file.

        Returns:
            Self for method chaining.
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning("Config file not found: %s", config_path)
            return self

        try:
            import yaml

            with open(path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}

            self._merge_config(yaml_config)
            self._config_paths.append(path)
            logger.info("Loaded configuration from %s", config_path)

        except ImportError:
            logger.error(
                "PyYAML not installed. Run: pip install pyyaml"
            )
        except Exception as e:
            logger.error("Failed to load config from YAML: %s", str(e))

        return self

    def load_from_env(self, prefix: str = "CHATBOT_") -> "ConfigLoader":
        """
        Load configuration from environment variables.

        Args:
            prefix: Prefix for environment variables.

        Returns:
            Self for method chaining.
        """
        env_mapping = {
            f"{prefix}OLLAMA_MODEL": ("ollama", "model_name"),
            f"{prefix}OLLAMA_BASE_URL": ("ollama", "base_url"),
            f"{prefix}OLLAMA_TIMEOUT": ("ollama", "timeout", int),
            f"{prefix}MEMORY_PERSISTENT": ("memory", "persistent_enabled",
                                           lambda x: x.lower() == "true"),
            f"{prefix}MEMORY_PATH": ("memory", "storage_path"),
            f"{prefix}LOG_LEVEL": ("logging", "level"),
            f"{prefix}LOG_FILE": ("logging", "file"),
            f"{prefix}SYSTEM_PROMPT": ("system_prompt",),
            f"{prefix}MAX_CONTEXT": ("max_context_messages", int),
        }

        for env_var, config_path in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert type if specified
                if len(config_path) > 2:
                    converter = config_path[2]
                    value = converter(value)

                # Set nested config value
                self._set_nested_value(list(config_path[:2]), value)
                logger.debug(
                    "Loaded config from env: %s = %s", env_var, value
                )

        return self

    def _set_nested_value(
        self, keys: List[str], value: Any
    ) -> None:
        """
        Set a nested value in the configuration dictionary.

        Args:
            keys: List of keys representing the path.
            value: Value to set.
        """
        current = self._config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """
        Merge new configuration into existing config.

        Args:
            new_config: New configuration dictionary to merge.
        """
        for key, value in new_config.items():
            if isinstance(value, dict) and key in self._config:
                if isinstance(self._config[key], dict):
                    self._config[key].update(value)
                else:
                    self._config[key] = value
            else:
                self._config[key] = value

    def get_chatbot_config(self) -> ChatBotConfig:
        """
        Get the complete ChatBot configuration.

        Returns:
            ChatBotConfig instance with all settings.
        """
        ollama_cfg = self._config.get("ollama", {})
        memory_cfg = self._config.get("memory", {})
        logging_cfg = self._config.get("logging", {})

        return ChatBotConfig(
            ollama=OllamaConfig(
                model_name=ollama_cfg.get("model_name", "llama3.2"),
                base_url=ollama_cfg.get("base_url", "http://localhost:11434"),
                timeout=ollama_cfg.get("timeout", 60),
                temperature=ollama_cfg.get("temperature", 0.7),
                top_p=ollama_cfg.get("top_p", 0.9),
            ),
            memory=MemoryConfig(
                volatile_enabled=memory_cfg.get("volatile_enabled", True),
                persistent_enabled=memory_cfg.get("persistent_enabled", False),
                storage_path=memory_cfg.get("storage_path",
                                            "./chatbot_memory"),
                max_entries=memory_cfg.get("max_entries", 1000),
            ),
            logging=LoggingConfig(
                level=logging_cfg.get("level", "INFO"),
                format=logging_cfg.get("format",
                                       "%(asctime)s - %(name)s - "
                                       "%(levelname)s - %(message)s"),
                file=logging_cfg.get("file"),
            ),
            system_prompt=self._config.get(
                "system_prompt",
                "You are a helpful, friendly, and knowledgeable assistant.",
            ),
            max_context_messages=self._config.get("max_context_messages", 10),
        )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key (dot-separated for nested).
            default: Default value if key not found.

        Returns:
            The configuration value or default.
        """
        keys = key.split(".")
        current = self._config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key (dot-separated for nested).
            value: Value to set.
        """
        self._set_nested_value(key.split("."), value)
        logger.debug("Set config: %s = %s", key, value)


def setup_logging(config: LoggingConfig) -> None:
    """
    Configure logging based on configuration.

    Args:
        config: Logging configuration.
    """
    log_level = getattr(logging, config.level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]

    if config.file:
        handlers.append(logging.FileHandler(config.file))

    logging.basicConfig(
        level=log_level,
        format=config.format,
        handlers=handlers,
    )

    logger.info("Logging configured at level %s", config.level)
