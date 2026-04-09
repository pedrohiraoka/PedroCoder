"""
Storage module for the async web scraper.
Handles saving extracted data to JSON or CSV files.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Exception raised for storage errors."""
    pass


class DataStorage:
    """
    Class for storing scraped data to files.
    
    Supports JSON and CSV output formats.
    """
    
    def __init__(self, output_file: str, output_format: str = 'json'):
        """
        Initialize the storage handler.
        
        Args:
            output_file: Path to the output file.
            output_format: Output format ('json' or 'csv').
        """
        self.output_file = Path(output_file)
        self.output_format = output_format.lower()
        self.data: List[Dict[str, Any]] = []
        
        if self.output_format not in ['json', 'csv']:
            raise StorageError(f"Unsupported output format: {output_format}")
        
        logger.debug(f"Initialized storage with format={output_format}, file={output_file}")
    
    def add(self, item: Dict[str, Any]) -> None:
        """
        Add a scraped item to the storage.
        
        Args:
            item: Dictionary containing scraped data.
        """
        self.data.append(item)
        logger.debug(f"Added item to storage (total: {len(self.data)})")
    
    def add_many(self, items: List[Dict[str, Any]]) -> None:
        """
        Add multiple scraped items to the storage.
        
        Args:
            items: List of dictionaries containing scraped data.
        """
        self.data.extend(items)
        logger.debug(f"Added {len(items)} items to storage (total: {len(self.data)})")
    
    def save(self) -> str:
        """
        Save all stored data to the output file.
        
        Returns:
            Path to the saved file.
            
        Raises:
            StorageError: If saving fails.
        """
        try:
            # Ensure parent directory exists
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if self.output_format == 'json':
                self._save_json()
            else:
                self._save_csv()
            
            logger.info(f"Saved {len(self.data)} items to {self.output_file}")
            return str(self.output_file)
        
        except Exception as e:
            raise StorageError(f"Failed to save data: {e}")
    
    def _save_json(self) -> None:
        """Save data to a JSON file."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        logger.debug(f"JSON data saved to {self.output_file}")
    
    def _save_csv(self) -> None:
        """Save data to a CSV file."""
        if not self.data:
            logger.warning("No data to save to CSV")
            return
        
        # Get all unique keys from all items
        fieldnames = set()
        for item in self.data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)
        
        with open(self.output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data)
        
        logger.debug(f"CSV data saved to {self.output_file} with fields: {fieldnames}")
    
    def clear(self) -> None:
        """Clear all stored data."""
        self.data.clear()
        logger.debug("Storage cleared")
    
    def __len__(self) -> int:
        """Return the number of items in storage."""
        return len(self.data)
    
    def __repr__(self) -> str:
        return f"DataStorage(format={self.output_format}, items={len(self.data)})"
