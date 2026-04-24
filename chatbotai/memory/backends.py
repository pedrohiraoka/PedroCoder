"""
Memory backends for ChatBotAI.

Provides both volatile (in-memory) and persistent (file-based) storage
for conversation history and context.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseMemory(ABC):
    """
    Abstract base class for memory implementations.

    Defines the interface for storing and retrieving conversation data.
    """

    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> None:
        """
        Save data to memory.

        Args:
            key: Unique identifier for the data.
            data: Data to store.
        """
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from memory.

        Args:
            key: The identifier for the data.

        Returns:
            The stored data or None if not found.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete data from memory.

        Args:
            key: The identifier for the data.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if data exists in memory.

        Args:
            key: The identifier for the data.

        Returns:
            True if exists, False otherwise.
        """
        pass

    @abstractmethod
    def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        List all keys in memory.

        Args:
            pattern: Optional pattern to filter keys.

        Returns:
            List of matching keys.
        """
        pass


class VolatileMemory(BaseMemory):
    """
    In-memory storage for temporary conversation data.

    This implementation stores data in RAM and is suitable for
    short-lived conversations or testing scenarios.
    """

    def __init__(self, max_entries: int = 1000) -> None:
        """
        Initialize volatile memory.

        Args:
            max_entries: Maximum number of entries to store.
        """
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._max_entries = max_entries
        logger.debug("Initialized VolatileMemory with max %d entries",
                     max_entries)

    def save(self, key: str, data: Dict[str, Any]) -> None:
        """
        Save data to volatile memory.

        Args:
            key: Unique identifier for the data.
            data: Data to store.
        """
        # Enforce max entries limit
        if len(self._storage) >= self._max_entries:
            # Remove oldest entry
            oldest_key = next(iter(self._storage))
            del self._storage[oldest_key]
            logger.debug("Removed oldest entry: %s", oldest_key)

        data_with_metadata = {
            **data,
            "_metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        }
        self._storage[key] = data_with_metadata
        logger.debug("Saved data to volatile memory: %s", key)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from volatile memory.

        Args:
            key: The identifier for the data.

        Returns:
            The stored data or None if not found.
        """
        data = self._storage.get(key)
        if data:
            logger.debug("Loaded data from volatile memory: %s", key)
            # Return without internal metadata
            return {k: v for k, v in data.items() if not k.startswith("_")}
        return None

    def delete(self, key: str) -> bool:
        """
        Delete data from volatile memory.

        Args:
            key: The identifier for the data.

        Returns:
            True if deleted, False if not found.
        """
        if key in self._storage:
            del self._storage[key]
            logger.debug("Deleted from volatile memory: %s", key)
            return True
        return False

    def exists(self, key: str) -> bool:
        """
        Check if data exists in volatile memory.

        Args:
            key: The identifier for the data.

        Returns:
            True if exists, False otherwise.
        """
        return key in self._storage

    def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        List all keys in volatile memory.

        Args:
            pattern: Optional pattern to filter keys.

        Returns:
            List of matching keys.
        """
        keys = list(self._storage.keys())
        if pattern:
            import fnmatch
            keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
        return keys

    def clear(self) -> None:
        """Clear all data from volatile memory."""
        self._storage.clear()
        logger.info("Cleared all volatile memory")


class PersistentMemory(BaseMemory):
    """
    File-based persistent storage for conversation data.

    This implementation stores data as JSON files, providing
    durability across application restarts.
    """

    def __init__(
        self,
        storage_path: str = "./chatbot_memory",
        file_extension: str = ".json",
    ) -> None:
        """
        Initialize persistent memory.

        Args:
            storage_path: Directory path for storing data files.
            file_extension: File extension for data files.
        """
        self._storage_path = Path(storage_path)
        self._file_extension = file_extension
        self._storage_path.mkdir(parents=True, exist_ok=True)
        logger.debug(
            "Initialized PersistentMemory at %s", self._storage_path
        )

    def _get_file_path(self, key: str) -> Path:
        """
        Get the file path for a given key.

        Args:
            key: The data identifier.

        Returns:
            Full file path for the data.
        """
        # Sanitize key to be filesystem-safe
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self._storage_path / f"{safe_key}{self._file_extension}"

    def save(self, key: str, data: Dict[str, Any]) -> None:
        """
        Save data to persistent storage.

        Args:
            key: Unique identifier for the data.
            data: Data to store.
        """
        file_path = self._get_file_path(key)

        data_with_metadata = {
            **data,
            "_metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "key": key,
            },
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_with_metadata, f, indent=2, ensure_ascii=False)
            logger.debug("Saved data to persistent memory: %s", key)
        except Exception as e:
            logger.error("Failed to save to persistent memory: %s", str(e))
            raise

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from persistent storage.

        Args:
            key: The identifier for the data.

        Returns:
            The stored data or None if not found.
        """
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug("Loaded data from persistent memory: %s", key)
            # Return without internal metadata
            return {k: v for k, v in data.items() if not k.startswith("_")}
        except Exception as e:
            logger.error("Failed to load from persistent memory: %s", str(e))
            return None

    def delete(self, key: str) -> bool:
        """
        Delete data from persistent storage.

        Args:
            key: The identifier for the data.

        Returns:
            True if deleted, False if not found.
        """
        file_path = self._get_file_path(key)

        if file_path.exists():
            try:
                file_path.unlink()
                logger.debug("Deleted from persistent memory: %s", key)
                return True
            except Exception as e:
                logger.error("Failed to delete from persistent memory: %s",
                             str(e))
                return False
        return False

    def exists(self, key: str) -> bool:
        """
        Check if data exists in persistent storage.

        Args:
            key: The identifier for the data.

        Returns:
            True if exists, False otherwise.
        """
        return self._get_file_path(key).exists()

    def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        List all keys in persistent storage.

        Args:
            pattern: Optional pattern to filter keys.

        Returns:
            List of matching keys.
        """
        keys = []
        for file_path in self._storage_path.glob(f"*{self._file_extension}"):
            key = file_path.stem
            if pattern is None or self._matches_pattern(key, pattern):
                keys.append(key)
        return keys

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """
        Check if a key matches a pattern.

        Args:
            key: The key to check.
            pattern: The pattern to match against.

        Returns:
            True if matches, False otherwise.
        """
        import fnmatch
        return fnmatch.fnmatch(key, pattern)

    def backup(self, backup_path: str) -> None:
        """
        Create a backup of all stored data.

        Args:
            backup_path: Directory path for the backup.
        """
        import shutil

        backup_dir = Path(backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        for file_path in self._storage_path.glob(f"*{self._file_extension}"):
            shutil.copy2(file_path, backup_dir / file_path.name)

        logger.info("Created backup at %s", backup_path)


class MemoryManager:
    """
    Manages multiple memory backends with automatic fallback.

    Provides a unified interface for memory operations with support
    for both volatile and persistent storage.
    """

    def __init__(
        self,
        volatile: bool = True,
        persistent: bool = False,
        storage_path: Optional[str] = None,
    ) -> None:
        """
        Initialize the memory manager.

        Args:
            volatile: Enable volatile memory backend.
            persistent: Enable persistent memory backend.
            storage_path: Path for persistent storage.
        """
        self._volatile: Optional[VolatileMemory] = None
        self._persistent: Optional[PersistentMemory] = None

        if volatile:
            self._volatile = VolatileMemory()

        if persistent:
            path = storage_path or "./chatbot_memory"
            self._persistent = PersistentMemory(storage_path=path)

        logger.info(
            "MemoryManager initialized: volatile=%s, persistent=%s",
            volatile,
            persistent,
        )

    def save(
        self, key: str, data: Dict[str, Any], priority: str = "volatile"
    ) -> None:
        """
        Save data to memory.

        Args:
            key: Unique identifier for the data.
            data: Data to store.
            priority: Which backend to use first ('volatile' or 'persistent').
        """
        if priority == "persistent" and self._persistent:
            self._persistent.save(key, data)
        elif self._volatile:
            self._volatile.save(key, data)

        # Save to both if available
        if priority == "volatile" and self._persistent:
            self._persistent.save(key, data)
        elif priority == "persistent" and self._volatile:
            self._volatile.save(key, data)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from memory.

        Args:
            key: The identifier for the data.

        Returns:
            The stored data or None if not found.
        """
        # Try volatile first (faster)
        if self._volatile:
            data = self._volatile.load(key)
            if data:
                return data

        # Fall back to persistent
        if self._persistent:
            return self._persistent.load(key)

        return None

    def delete(self, key: str) -> bool:
        """
        Delete data from all memory backends.

        Args:
            key: The identifier for the data.

        Returns:
            True if deleted from any backend.
        """
        deleted = False

        if self._volatile:
            deleted = self._volatile.delete(key) or deleted

        if self._persistent:
            deleted = self._persistent.delete(key) or deleted

        return deleted

    def exists(self, key: str) -> bool:
        """
        Check if data exists in any memory backend.

        Args:
            key: The identifier for the data.

        Returns:
            True if exists in any backend.
        """
        if self._volatile and self._volatile.exists(key):
            return True

        if self._persistent and self._persistent.exists(key):
            return True

        return False
