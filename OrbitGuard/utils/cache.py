"""
Cache management for OrbitGuard using SQLite and Parquet.

This module provides caching mechanisms for API responses to reduce
API calls and improve performance.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Dict, List
import logging

from utils.config import config

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages local cache for API responses using SQLite.

    Provides methods to store, retrieve, and invalidate cached data
    with automatic expiration handling.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the cache manager.

        Args:
            db_path: Path to SQLite database. Uses config default if None.
        """
        self.db_path = db_path or config.cache_db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_cache (
                    id TEXT PRIMARY KEY,
                    endpoint TEXT NOT NULL,
                    query_hash TEXT NOT NULL,
                    response_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_endpoint 
                ON api_cache(endpoint)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires 
                ON api_cache(expires_at)
            """)
            conn.commit()

    def _generate_key(self, endpoint: str, query_params: Dict[str, Any]) -> str:
        """
        Generate a unique cache key from endpoint and query parameters.

        Args:
            endpoint: API endpoint identifier.
            query_params: Dictionary of query parameters.

        Returns:
            SHA256 hash of the serialized query.
        """
        # Sort keys for consistent hashing
        sorted_params = json.dumps(query_params, sort_keys=True, default=str)
        key_string = f"{endpoint}:{sorted_params}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _now_utc(self) -> datetime:
        """Get current UTC time."""
        return datetime.now(timezone.utc)

    def get(
        self, 
        endpoint: str, 
        query_params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Retrieve cached data if available and not expired.

        Args:
            endpoint: API endpoint identifier.
            query_params: Query parameters used for the original request.

        Returns:
            Cached response data or None if not found/expired.
        """
        cache_key = self._generate_key(endpoint, query_params)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT response_data FROM api_cache WHERE id = ? AND expires_at > ?",
                (cache_key, self._now_utc().isoformat())
            )
            row = cursor.fetchone()
            
            if row:
                logger.debug(f"Cache hit for {endpoint}")
                return json.loads(row["response_data"])
            
            logger.debug(f"Cache miss for {endpoint}")
            return None

    def set(
        self,
        endpoint: str,
        query_params: Dict[str, Any],
        data: Any,
        expiry_hours: Optional[int] = None
    ) -> None:
        """
        Store data in cache with expiration.

        Args:
            endpoint: API endpoint identifier.
            query_params: Query parameters for the request.
            data: Response data to cache (must be JSON-serializable).
            expiry_hours: Hours until expiration. Uses config default if None.
        """
        cache_key = self._generate_key(endpoint, query_params)
        expiry = expiry_hours or config.CACHE_EXPIRY_HOURS
        expires_at = (self._now_utc() + timedelta(hours=expiry)).isoformat()
        
        try:
            serialized = json.dumps(data, default=str)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize data for caching: {e}")
            return
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO api_cache 
                (id, endpoint, query_hash, response_data, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (cache_key, endpoint, cache_key, serialized, expires_at)
            )
            conn.commit()
        
        logger.debug(f"Cached data for {endpoint} (expires in {expiry}h)")

    def invalidate(self, endpoint: Optional[str] = None) -> int:
        """
        Invalidate cached entries.

        Args:
            endpoint: Specific endpoint to invalidate. If None, clears all.

        Returns:
            Number of entries invalidated.
        """
        with sqlite3.connect(self.db_path) as conn:
            if endpoint:
                cursor = conn.execute(
                    "DELETE FROM api_cache WHERE endpoint = ?",
                    (endpoint,)
                )
            else:
                cursor = conn.execute("DELETE FROM api_cache")
            
            conn.commit()
            count = cursor.rowcount
        
        logger.info(f"Invalidated {count} cache entries")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM api_cache WHERE expires_at <= ?",
                (self._now_utc().isoformat(),)
            )
            conn.commit()
            count = cursor.rowcount
        
        if count > 0:
            logger.debug(f"Cleaned up {count} expired cache entries")
        
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM api_cache"
            ).fetchone()[0]
            
            expired = conn.execute(
                "SELECT COUNT(*) FROM api_cache WHERE expires_at <= ?",
                (self._now_utc().isoformat(),)
            ).fetchone()[0]
            
            by_endpoint = conn.execute(
                "SELECT endpoint, COUNT(*) as count FROM api_cache GROUP BY endpoint"
            ).fetchall()
        
        return {
            "total_entries": total,
            "expired_entries": expired,
            "valid_entries": total - expired,
            "by_endpoint": dict(by_endpoint),
            "db_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        }


# Global cache instance
cache_manager = CacheManager()
