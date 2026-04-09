"""
Configuration module for the async web scraper.
Handles loading and validating configuration from YAML or JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class ScraperConfig:
    """
    Configuration class for the web scraper.
    
    Attributes:
        urls (List[str]): List of URLs to scrape.
        headers (Dict[str, str]): HTTP headers for requests.
        delay (float): Delay between requests in seconds.
        timeout (int): Request timeout in seconds.
        selectors (Dict[str, str]): CSS/XPath selectors for data extraction.
        follow_links (bool): Whether to follow links on pages.
        link_selectors (List[str]): Selectors for extracting links.
        max_concurrent (int): Maximum number of concurrent requests.
        output_file (str): Path to output file.
        output_format (str): Output format ('json' or 'csv').
    """
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize configuration from a dictionary.
        
        Args:
            config_data: Dictionary containing configuration values.
        """
        self.urls: List[str] = config_data.get('urls', [])
        self.headers: Dict[str, str] = config_data.get('headers', {
            'User-Agent': 'Mozilla/5.0 (compatible; AsyncScraper/1.0)'
        })
        self.delay: float = config_data.get('delay', 1.0)
        self.timeout: int = config_data.get('timeout', 30)
        self.selectors: Dict[str, str] = config_data.get('selectors', {})
        self.follow_links: bool = config_data.get('follow_links', False)
        self.link_selectors: List[str] = config_data.get('link_selectors', ['a[href]'])
        self.max_concurrent: int = config_data.get('max_concurrent', 10)
        self.output_file: str = config_data.get('output_file', 'output.json')
        self.output_format: str = config_data.get('output_format', 'json')
        
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate the configuration.
        
        Raises:
            ConfigError: If configuration is invalid.
        """
        if not self.urls:
            raise ConfigError("At least one URL must be specified in 'urls'")
        
        if self.delay < 0:
            raise ConfigError("Delay must be non-negative")
        
        if self.timeout <= 0:
            raise ConfigError("Timeout must be positive")
        
        if self.max_concurrent <= 0:
            raise ConfigError("Max concurrent requests must be positive")
        
        if self.output_format not in ['json', 'csv']:
            raise ConfigError("Output format must be 'json' or 'csv'")
        
        logger.debug("Configuration validated successfully")
    
    @classmethod
    def from_yaml(cls, filepath: str) -> 'ScraperConfig':
        """
        Load configuration from a YAML file.
        
        Args:
            filepath: Path to the YAML configuration file.
            
        Returns:
            ScraperConfig instance.
            
        Raises:
            ConfigError: If file cannot be read or parsed.
        """
        try:
            path = Path(filepath)
            if not path.exists():
                raise ConfigError(f"Configuration file not found: {filepath}")
            
            with open(path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not isinstance(config_data, dict):
                raise ConfigError("YAML file must contain a dictionary")
            
            logger.info(f"Loaded configuration from {filepath}")
            return cls(config_data)
        
        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing YAML file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")
    
    @classmethod
    def from_json(cls, filepath: str) -> 'ScraperConfig':
        """
        Load configuration from a JSON file.
        
        Args:
            filepath: Path to the JSON configuration file.
            
        Returns:
            ScraperConfig instance.
            
        Raises:
            ConfigError: If file cannot be read or parsed.
        """
        try:
            path = Path(filepath)
            if not path.exists():
                raise ConfigError(f"Configuration file not found: {filepath}")
            
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if not isinstance(config_data, dict):
                raise ConfigError("JSON file must contain a dictionary")
            
            logger.info(f"Loaded configuration from {filepath}")
            return cls(config_data)
        
        except json.JSONDecodeError as e:
            raise ConfigError(f"Error parsing JSON file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")
    
    @classmethod
    def load(cls, filepath: str) -> 'ScraperConfig':
        """
        Load configuration from a file (auto-detect format).
        
        Args:
            filepath: Path to the configuration file.
            
        Returns:
            ScraperConfig instance.
        """
        path = Path(filepath)
        suffix = path.suffix.lower()
        
        if suffix in ['.yaml', '.yml']:
            return cls.from_yaml(filepath)
        elif suffix == '.json':
            return cls.from_json(filepath)
        else:
            raise ConfigError(f"Unsupported configuration file format: {suffix}")
    
    def __repr__(self) -> str:
        return f"ScraperConfig(urls={len(self.urls)}, output={self.output_file})"
