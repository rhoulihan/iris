"""Unit tests for Redis cache implementation.

This module tests the RedisCache class which provides in-memory caching
using Redis as the backend store.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_redis():
    """Provide a mock Redis client."""
    with patch("redis.Redis") as mock_redis_class:
        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client
        yield mock_client


class TestRedisCacheInitialization:
    """Test RedisCache initialization."""

    @pytest.mark.unit
    def test_cache_initialization_default_params(self, mock_redis):
        """Test RedisCache initialization with default parameters."""
        from src.common.cache_interface import RedisCache

        cache = RedisCache()

        assert cache is not None
        assert cache.client == mock_redis

    @pytest.mark.unit
    def test_cache_initialization_custom_params(self):
        """Test RedisCache initialization with custom parameters."""
        from src.common.cache_interface import RedisCache

        with patch("redis.Redis") as mock_redis_class:
            mock_client = MagicMock()
            mock_redis_class.return_value = mock_client

            cache = RedisCache(host="redis.example.com", port=6380, db=5)

            mock_redis_class.assert_called_once_with(
                host="redis.example.com", port=6380, db=5, decode_responses=False
            )
            assert cache.client == mock_client


class TestRedisCacheGet:
    """Test cache retrieval operations."""

    @pytest.mark.unit
    def test_get_existing_key(self, mock_redis):
        """Test retrieving existing key from cache."""
        import pickle

        from src.common.cache_interface import RedisCache

        test_value = {"name": "Alice", "age": 30}
        mock_redis.get.return_value = pickle.dumps(test_value)

        cache = RedisCache()
        result = cache.get("user:123")

        assert result == test_value
        mock_redis.get.assert_called_once_with("user:123")

    @pytest.mark.unit
    def test_get_nonexistent_key(self, mock_redis):
        """Test retrieving non-existent key returns None."""
        from src.common.cache_interface import RedisCache

        mock_redis.get.return_value = None

        cache = RedisCache()
        result = cache.get("nonexistent")

        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent")

    @pytest.mark.unit
    def test_get_complex_data_structure(self, mock_redis):
        """Test retrieving complex data structures."""
        import pickle

        from src.common.cache_interface import RedisCache

        test_value = {
            "queries": [
                {"sql_id": "abc", "executions": 100},
                {"sql_id": "def", "executions": 50},
            ],
            "metadata": {"compressed": True, "count": 2},
        }
        mock_redis.get.return_value = pickle.dumps(test_value)

        cache = RedisCache()
        result = cache.get("workload:batch1")

        assert result == test_value
        assert result["queries"][0]["sql_id"] == "abc"


class TestRedisCacheSet:
    """Test cache storage operations."""

    @pytest.mark.unit
    def test_set_without_ttl(self, mock_redis):
        """Test setting value without TTL."""
        import pickle

        from src.common.cache_interface import RedisCache

        test_value = {"name": "Bob", "age": 25}

        cache = RedisCache()
        cache.set("user:456", test_value)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "user:456"
        assert pickle.loads(call_args[0][1]) == test_value

    @pytest.mark.unit
    def test_set_with_ttl(self, mock_redis):
        """Test setting value with TTL."""
        import pickle

        from src.common.cache_interface import RedisCache

        test_value = {"session_id": "xyz789"}
        ttl_seconds = 3600

        cache = RedisCache()
        cache.set("session:xyz", test_value, ttl=ttl_seconds)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "session:xyz"
        assert call_args[0][1] == ttl_seconds
        assert pickle.loads(call_args[0][2]) == test_value

    @pytest.mark.unit
    def test_set_overwrites_existing_key(self, mock_redis):
        """Test that setting existing key overwrites the value."""
        import pickle

        from src.common.cache_interface import RedisCache

        cache = RedisCache()
        cache.set("counter", 1)
        cache.set("counter", 2)

        assert mock_redis.set.call_count == 2
        last_call = mock_redis.set.call_args
        assert pickle.loads(last_call[0][1]) == 2

    @pytest.mark.unit
    def test_set_none_value(self, mock_redis):
        """Test setting None as a value."""
        import pickle

        from src.common.cache_interface import RedisCache

        cache = RedisCache()
        cache.set("nullable", None)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert pickle.loads(call_args[0][1]) is None


class TestRedisCacheDelete:
    """Test cache deletion operations."""

    @pytest.mark.unit
    def test_delete_existing_key(self, mock_redis):
        """Test deleting existing key from cache."""
        from src.common.cache_interface import RedisCache

        mock_redis.delete.return_value = 1

        cache = RedisCache()
        cache.delete("user:123")

        mock_redis.delete.assert_called_once_with("user:123")

    @pytest.mark.unit
    def test_delete_nonexistent_key(self, mock_redis):
        """Test deleting non-existent key does not raise error."""
        from src.common.cache_interface import RedisCache

        mock_redis.delete.return_value = 0

        cache = RedisCache()
        cache.delete("nonexistent")

        mock_redis.delete.assert_called_once_with("nonexistent")

    @pytest.mark.unit
    def test_delete_multiple_keys(self, mock_redis):
        """Test deleting multiple keys sequentially."""
        from src.common.cache_interface import RedisCache

        cache = RedisCache()
        cache.delete("key1")
        cache.delete("key2")
        cache.delete("key3")

        assert mock_redis.delete.call_count == 3


class TestRedisCacheExists:
    """Test cache existence checking operations."""

    @pytest.mark.unit
    def test_exists_returns_true_for_existing_key(self, mock_redis):
        """Test exists returns True for existing key."""
        from src.common.cache_interface import RedisCache

        mock_redis.exists.return_value = 1

        cache = RedisCache()
        result = cache.exists("user:123")

        assert result is True
        mock_redis.exists.assert_called_once_with("user:123")

    @pytest.mark.unit
    def test_exists_returns_false_for_nonexistent_key(self, mock_redis):
        """Test exists returns False for non-existent key."""
        from src.common.cache_interface import RedisCache

        mock_redis.exists.return_value = 0

        cache = RedisCache()
        result = cache.exists("nonexistent")

        assert result is False
        mock_redis.exists.assert_called_once_with("nonexistent")

    @pytest.mark.unit
    def test_exists_after_set(self, mock_redis):
        """Test exists returns True after setting a key."""
        from src.common.cache_interface import RedisCache

        mock_redis.exists.return_value = 1

        cache = RedisCache()
        cache.set("new_key", "value")
        result = cache.exists("new_key")

        assert result is True


class TestRedisCacheIntegration:
    """Test cache operations working together."""

    @pytest.mark.unit
    def test_set_get_delete_workflow(self, mock_redis):
        """Test complete set-get-delete workflow."""
        import pickle

        from src.common.cache_interface import RedisCache

        test_data = {"workflow": "test"}
        mock_redis.get.return_value = pickle.dumps(test_data)
        mock_redis.exists.return_value = 1

        cache = RedisCache()

        # Set
        cache.set("workflow:test", test_data)
        assert mock_redis.set.called

        # Get
        result = cache.get("workflow:test")
        assert result == test_data

        # Exists
        exists = cache.exists("workflow:test")
        assert exists is True

        # Delete
        cache.delete("workflow:test")
        assert mock_redis.delete.called

    @pytest.mark.unit
    def test_ttl_behavior(self, mock_redis):
        """Test TTL is respected in set operations."""
        from src.common.cache_interface import RedisCache

        cache = RedisCache()

        # Set without TTL
        cache.set("permanent", "value")
        assert mock_redis.set.called
        assert not mock_redis.setex.called

        mock_redis.reset_mock()

        # Set with TTL
        cache.set("temporary", "value", ttl=60)
        assert mock_redis.setex.called
        assert not mock_redis.set.called


class TestCacheBackendFactory:
    """Test cache backend factory function."""

    @pytest.mark.unit
    def test_get_development_backend(self):
        """Test getting development cache backend."""
        from src.common.cache_interface import RedisCache, get_cache_backend

        with patch("redis.Redis"):
            cache = get_cache_backend("development")
            assert isinstance(cache, RedisCache)

    @pytest.mark.unit
    def test_get_testing_backend(self):
        """Test getting testing cache backend."""
        from src.common.cache_interface import RedisCache, get_cache_backend

        with patch("redis.Redis"):
            cache = get_cache_backend("testing")
            assert isinstance(cache, RedisCache)

    @pytest.mark.unit
    def test_get_development_with_custom_config(self):
        """Test getting development backend with custom config."""
        from src.common.cache_interface import RedisCache, get_cache_backend

        with patch("redis.Redis") as mock_redis:
            cache = get_cache_backend("development", host="custom.redis.com", port=6380, db=2)
            assert isinstance(cache, RedisCache)
            mock_redis.assert_called_with(
                host="custom.redis.com", port=6380, db=2, decode_responses=False
            )

    @pytest.mark.unit
    def test_get_production_backend_requires_dsn(self):
        """Test that production backend requires DSN."""
        from src.common.cache_interface import get_cache_backend

        with pytest.raises(ValueError, match="TimesTen DSN required"):
            get_cache_backend("production")

    @pytest.mark.unit
    def test_unknown_environment_raises_error(self):
        """Test that unknown environment raises ValueError."""
        from src.common.cache_interface import get_cache_backend

        with pytest.raises(ValueError, match="Unknown environment"):
            get_cache_backend("staging")


class TestCacheDataTypes:
    """Test caching different Python data types."""

    @pytest.mark.unit
    def test_cache_string(self, mock_redis):
        """Test caching string values."""
        import pickle

        from src.common.cache_interface import RedisCache

        test_value = "Hello, World!"
        mock_redis.get.return_value = pickle.dumps(test_value)

        cache = RedisCache()
        cache.set("greeting", test_value)
        result = cache.get("greeting")

        assert result == test_value

    @pytest.mark.unit
    def test_cache_integer(self, mock_redis):
        """Test caching integer values."""
        import pickle

        from src.common.cache_interface import RedisCache

        test_value = 42
        mock_redis.get.return_value = pickle.dumps(test_value)

        cache = RedisCache()
        cache.set("answer", test_value)
        result = cache.get("answer")

        assert result == test_value

    @pytest.mark.unit
    def test_cache_list(self, mock_redis):
        """Test caching list values."""
        import pickle

        from src.common.cache_interface import RedisCache

        test_value = [1, 2, 3, "four", 5.0]
        mock_redis.get.return_value = pickle.dumps(test_value)

        cache = RedisCache()
        cache.set("numbers", test_value)
        result = cache.get("numbers")

        assert result == test_value

    @pytest.mark.unit
    def test_cache_dict(self, mock_redis):
        """Test caching dictionary values."""
        import pickle

        from src.common.cache_interface import RedisCache

        test_value = {"key1": "value1", "key2": 123, "nested": {"a": 1}}
        mock_redis.get.return_value = pickle.dumps(test_value)

        cache = RedisCache()
        cache.set("config", test_value)
        result = cache.get("config")

        assert result == test_value


class TestTimesTenCacheInitialization:
    """Test TimesTenCache initialization."""

    @pytest.mark.unit
    def test_timesten_cache_initialization(self):
        """Test TimesTenCache initialization with mocked oracle db."""
        from src.common.cache_interface import TimesTenCache

        with patch("oracledb.connect") as mock_connect:
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection

            cache = TimesTenCache(dsn="localhost/TTDB")

            mock_connect.assert_called_once_with("localhost/TTDB")
            assert cache.connection == mock_connection


class TestTimesTenCacheOperations:
    """Test TimesTenCache get/set/delete operations."""

    @pytest.mark.unit
    def test_timesten_get_existing_key(self):
        """Test getting an existing key from TimesTen cache."""
        import pickle

        from src.common.cache_interface import TimesTenCache

        with patch("oracledb.connect") as mock_connect:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

            test_value = {"data": "test"}
            # Mock BLOB object with read() method
            mock_blob = MagicMock()
            mock_blob.read.return_value = pickle.dumps(test_value)
            mock_cursor.fetchone.return_value = (mock_blob,)

            mock_connect.return_value = mock_connection

            cache = TimesTenCache(dsn="localhost/TTDB")
            result = cache.get("test_key")

            assert result == test_value

    @pytest.mark.unit
    def test_timesten_get_nonexistent_key(self):
        """Test getting a non-existent key returns None."""
        from src.common.cache_interface import TimesTenCache

        with patch("oracledb.connect") as mock_connect:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchone.return_value = None

            mock_connect.return_value = mock_connection

            cache = TimesTenCache(dsn="localhost/TTDB")
            result = cache.get("nonexistent")

            assert result is None

    @pytest.mark.unit
    def test_timesten_set_value(self):
        """Test setting a value in TimesTen cache."""
        from src.common.cache_interface import TimesTenCache

        with patch("oracledb.connect") as mock_connect:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

            mock_connect.return_value = mock_connection

            cache = TimesTenCache(dsn="localhost/TTDB")
            cache.set("test_key", "test_value", ttl=3600)

            # Verify execute was called (for INSERT/UPDATE)
            assert mock_cursor.execute.called
            mock_connection.commit.assert_called()

    @pytest.mark.unit
    def test_timesten_delete_key(self):
        """Test deleting a key from TimesTen cache."""
        from src.common.cache_interface import TimesTenCache

        with patch("oracledb.connect") as mock_connect:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

            mock_connect.return_value = mock_connection

            cache = TimesTenCache(dsn="localhost/TTDB")
            cache.delete("test_key")

            # Verify DELETE was called
            assert mock_cursor.execute.called
            mock_connection.commit.assert_called()
