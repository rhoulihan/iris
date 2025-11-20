"""Cache abstraction layer for IRIS project.

Provides unified interface for in-memory caching across different backends:
- Redis (development and simple caching)
- Oracle TimesTen In-Memory Database (production)
"""

import pickle  # nosec B403
from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheInterface(ABC):
    """Abstract interface for in-memory caching."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value with optional TTL in seconds.

        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time-to-live in seconds (None = no expiration)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete key from cache.

        Args:
            key: Cache key to delete
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and is not expired
        """
        pass


class RedisCache(CacheInterface):
    """Redis-based cache for development and simple use cases."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize Redis cache.

        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
        """
        import redis

        self.client = redis.Redis(
            host=host, port=port, db=db, decode_responses=False  # Keep binary mode for pickle
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        data = self.client.get(key)
        return pickle.loads(data) if data else None  # nosec B301

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis cache with optional TTL."""
        serialized = pickle.dumps(value)
        if ttl:
            self.client.setex(key, ttl, serialized)
        else:
            self.client.set(key, serialized)

    def delete(self, key: str) -> None:
        """Delete key from Redis cache."""
        self.client.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        return bool(self.client.exists(key))


class TimesTenCache(CacheInterface):
    """Oracle TimesTen In-Memory Database cache for production.

    Note: Requires Oracle TimesTen to be installed and configured.
    """

    def __init__(self, dsn: str):
        """Initialize TimesTen cache.

        Args:
            dsn: TimesTen data source name
        """
        import oracledb

        self.connection = oracledb.connect(dsn)
        self._ensure_cache_table()

    def _ensure_cache_table(self):
        """Create cache table if it doesn't exist."""
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    CREATE TABLE cache_store (
                        cache_key VARCHAR2(255) PRIMARY KEY,
                        cache_value BLOB,
                        expiry_time TIMESTAMP
                    )
                """
                )
                self.connection.commit()
            except Exception:  # nosec B110
                # Table already exists - this is expected behavior
                pass

    def get(self, key: str) -> Optional[Any]:
        """Get value from TimesTen cache."""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT cache_value FROM cache_store
                WHERE cache_key = :key
                AND (expiry_time IS NULL OR expiry_time > SYSTIMESTAMP)
            """,
                key=key,
            )
            row = cursor.fetchone()
            return pickle.loads(row[0].read()) if row else None  # nosec B301

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in TimesTen cache with optional TTL."""
        serialized = pickle.dumps(value)

        with self.connection.cursor() as cursor:
            if ttl:
                cursor.execute(
                    """
                    MERGE INTO cache_store USING DUAL ON (cache_key = :key)
                    WHEN MATCHED THEN
                        UPDATE SET cache_value = :value,
                                   expiry_time = SYSTIMESTAMP + INTERVAL :ttl SECOND
                    WHEN NOT MATCHED THEN
                        INSERT (cache_key, cache_value, expiry_time)
                        VALUES (:key, :value, SYSTIMESTAMP + INTERVAL :ttl SECOND)
                """,
                    key=key,
                    value=serialized,
                    ttl=ttl,
                )
            else:
                cursor.execute(
                    """
                    MERGE INTO cache_store USING DUAL ON (cache_key = :key)
                    WHEN MATCHED THEN
                        UPDATE SET cache_value = :value, expiry_time = NULL
                    WHEN NOT MATCHED THEN
                        INSERT (cache_key, cache_value, expiry_time)
                        VALUES (:key, :value, NULL)
                """,
                    key=key,
                    value=serialized,
                )
            self.connection.commit()

    def delete(self, key: str) -> None:
        """Delete key from TimesTen cache."""
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM cache_store WHERE cache_key = :key", key=key)
            self.connection.commit()

    def exists(self, key: str) -> bool:
        """Check if key exists in TimesTen cache."""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM cache_store
                WHERE cache_key = :key
                AND (expiry_time IS NULL OR expiry_time > SYSTIMESTAMP)
            """,
                key=key,
            )
            return cursor.fetchone() is not None


def get_cache_backend(env: str = "development", **kwargs) -> CacheInterface:
    """Get appropriate cache backend for the given environment.

    Args:
        env: Environment name (development, testing, production)
        **kwargs: Additional backend-specific configuration

    Returns:
        CacheInterface implementation for the specified environment

    Example:
        >>> cache = get_cache_backend("development")
        >>> cache.set("user:123", {"name": "Alice"}, ttl=3600)
        >>> user_data = cache.get("user:123")
    """
    if env in ["development", "testing"]:
        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", 6379)
        db = kwargs.get("db", 0)
        return RedisCache(host=host, port=port, db=db)

    elif env == "production":
        dsn = kwargs.get("dsn")
        if not dsn:
            raise ValueError("TimesTen DSN required for production environment")
        return TimesTenCache(dsn=dsn)

    else:
        raise ValueError(f"Unknown environment: {env}")
