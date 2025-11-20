"""Unit tests for storage implementations.

This module tests LocalFilesystemStorage and MinIOStorage classes which provide
object storage capabilities for the IRIS project.
"""

import io
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_storage_path(tmp_path):
    """Provide a temporary directory for filesystem storage."""
    return tmp_path / "test_storage"


@pytest.fixture
def mock_s3_client():
    """Provide a mock S3/MinIO client."""
    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        yield mock_client


class TestLocalFilesystemStorageInitialization:
    """Test LocalFilesystemStorage initialization."""

    @pytest.mark.unit
    def test_storage_initialization(self, temp_storage_path):
        """Test storage initialization creates base directory."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)

        assert storage is not None
        assert storage.base_path == temp_storage_path
        assert temp_storage_path.exists()

    @pytest.mark.unit
    def test_storage_creates_nested_directories(self, tmp_path):
        """Test storage creates nested directory structure if needed."""
        from src.common.storage_interface import LocalFilesystemStorage

        nested_path = tmp_path / "level1" / "level2" / "level3"
        storage = LocalFilesystemStorage(nested_path)

        assert nested_path.exists()
        assert storage.base_path == nested_path


class TestLocalFilesystemPutObject:
    """Test put_object operations for local filesystem."""

    @pytest.mark.unit
    def test_put_object_creates_file(self, temp_storage_path):
        """Test putting object creates file in correct location."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)
        test_data = b"Hello, World!"
        data_stream = io.BytesIO(test_data)

        storage.put_object("test-bucket", "test-file.txt", data_stream)

        target_file = temp_storage_path / "test-bucket" / "test-file.txt"
        assert target_file.exists()
        assert target_file.read_bytes() == test_data

    @pytest.mark.unit
    def test_put_object_with_nested_key(self, temp_storage_path):
        """Test putting object with nested key path."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)
        test_data = b"Nested content"
        data_stream = io.BytesIO(test_data)

        storage.put_object("bucket", "dir1/dir2/file.dat", data_stream)

        target_file = temp_storage_path / "bucket" / "dir1" / "dir2" / "file.dat"
        assert target_file.exists()
        assert target_file.read_bytes() == test_data

    @pytest.mark.unit
    def test_put_object_overwrites_existing(self, temp_storage_path):
        """Test putting object overwrites existing file."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)

        # Put initial object
        storage.put_object("bucket", "file.txt", io.BytesIO(b"version 1"))

        # Overwrite with new content
        storage.put_object("bucket", "file.txt", io.BytesIO(b"version 2"))

        target_file = temp_storage_path / "bucket" / "file.txt"
        assert target_file.read_bytes() == b"version 2"


class TestLocalFilesystemGetObject:
    """Test get_object operations for local filesystem."""

    @pytest.mark.unit
    def test_get_existing_object(self, temp_storage_path):
        """Test getting existing object returns correct data."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)
        test_data = b"Test content for retrieval"

        # Put object first
        storage.put_object("bucket", "file.txt", io.BytesIO(test_data))

        # Get object
        retrieved_data = storage.get_object("bucket", "file.txt")

        assert retrieved_data == test_data

    @pytest.mark.unit
    def test_get_nonexistent_object_raises_error(self, temp_storage_path):
        """Test getting non-existent object raises FileNotFoundError."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)

        with pytest.raises(FileNotFoundError):
            storage.get_object("bucket", "nonexistent.txt")

    @pytest.mark.unit
    def test_get_object_from_nonexistent_bucket(self, temp_storage_path):
        """Test getting object from non-existent bucket raises error."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)

        with pytest.raises(FileNotFoundError):
            storage.get_object("nonexistent-bucket", "file.txt")


class TestLocalFilesystemDeleteObject:
    """Test delete_object operations for local filesystem."""

    @pytest.mark.unit
    def test_delete_existing_object(self, temp_storage_path):
        """Test deleting existing object removes file."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)

        # Put object first
        storage.put_object("bucket", "to-delete.txt", io.BytesIO(b"data"))

        target_file = temp_storage_path / "bucket" / "to-delete.txt"
        assert target_file.exists()

        # Delete object
        storage.delete_object("bucket", "to-delete.txt")

        assert not target_file.exists()

    @pytest.mark.unit
    def test_delete_nonexistent_object_succeeds(self, temp_storage_path):
        """Test deleting non-existent object does not raise error."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)

        # Should not raise error
        storage.delete_object("bucket", "nonexistent.txt")


class TestLocalFilesystemListObjects:
    """Test list_objects operations for local filesystem."""

    @pytest.mark.unit
    def test_list_objects_in_empty_bucket(self, temp_storage_path):
        """Test listing objects in empty bucket returns empty list."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)
        (temp_storage_path / "empty-bucket").mkdir()

        result = storage.list_objects("empty-bucket")

        assert result == []

    @pytest.mark.unit
    def test_list_objects_in_nonexistent_bucket(self, temp_storage_path):
        """Test listing objects in non-existent bucket returns empty list."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)

        result = storage.list_objects("nonexistent-bucket")

        assert result == []

    @pytest.mark.unit
    def test_list_all_objects(self, temp_storage_path):
        """Test listing all objects in bucket."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)

        # Put multiple objects
        storage.put_object("bucket", "file1.txt", io.BytesIO(b"data1"))
        storage.put_object("bucket", "file2.txt", io.BytesIO(b"data2"))
        storage.put_object("bucket", "dir/file3.txt", io.BytesIO(b"data3"))

        result = storage.list_objects("bucket")

        assert len(result) == 3
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "dir/file3.txt" in result or "dir\\file3.txt" in result  # Windows compat

    @pytest.mark.unit
    def test_list_objects_with_prefix(self, temp_storage_path):
        """Test listing objects with prefix filter."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)

        # Put objects with different prefixes
        storage.put_object("bucket", "logs/app.log", io.BytesIO(b"log1"))
        storage.put_object("bucket", "logs/error.log", io.BytesIO(b"log2"))
        storage.put_object("bucket", "data/file.csv", io.BytesIO(b"csv"))

        result = storage.list_objects("bucket", prefix="logs")

        assert len(result) == 2
        assert any("logs" in r for r in result)


class TestMinIOStorageInitialization:
    """Test MinIOStorage initialization."""

    @pytest.mark.unit
    def test_storage_initialization(self, mock_s3_client):
        """Test MinIO storage initialization."""
        from src.common.storage_interface import MinIOStorage

        storage = MinIOStorage(
            endpoint="http://localhost:9000",
            access_key="test-key",
            secret_key="test-secret",
        )

        assert storage is not None
        assert storage.s3 == mock_s3_client

    @pytest.mark.unit
    def test_initialization_creates_s3_client(self):
        """Test that initialization creates boto3 S3 client."""
        from src.common.storage_interface import MinIOStorage

        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            storage = MinIOStorage(
                endpoint="http://minio.example.com:9000",
                access_key="admin",
                secret_key="password",
            )

            assert storage is not None
            mock_boto.assert_called_once()
            call_kwargs = mock_boto.call_args[1]
            assert call_kwargs["endpoint_url"] == "http://minio.example.com:9000"
            assert call_kwargs["aws_access_key_id"] == "admin"
            assert call_kwargs["aws_secret_access_key"] == "password"


class TestMinIOPutObject:
    """Test put_object operations for MinIO."""

    @pytest.mark.unit
    def test_put_object(self, mock_s3_client):
        """Test putting object to MinIO."""
        from src.common.storage_interface import MinIOStorage

        storage = MinIOStorage("http://localhost:9000", "key", "secret")
        test_data = b"MinIO test data"
        data_stream = io.BytesIO(test_data)

        storage.put_object("test-bucket", "test-key", data_stream)

        mock_s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket", Key="test-key", Body=data_stream
        )

    @pytest.mark.unit
    def test_put_object_with_nested_key(self, mock_s3_client):
        """Test putting object with nested key path."""
        from src.common.storage_interface import MinIOStorage

        storage = MinIOStorage("http://localhost:9000", "key", "secret")
        data_stream = io.BytesIO(b"nested data")

        storage.put_object("bucket", "path/to/object.dat", data_stream)

        mock_s3_client.put_object.assert_called_once_with(
            Bucket="bucket", Key="path/to/object.dat", Body=data_stream
        )


class TestMinIOGetObject:
    """Test get_object operations for MinIO."""

    @pytest.mark.unit
    def test_get_object(self, mock_s3_client):
        """Test getting object from MinIO."""
        from src.common.storage_interface import MinIOStorage

        test_data = b"Retrieved data"
        mock_response = {"Body": io.BytesIO(test_data)}
        mock_s3_client.get_object.return_value = mock_response

        storage = MinIOStorage("http://localhost:9000", "key", "secret")
        result = storage.get_object("bucket", "key")

        assert result == test_data
        mock_s3_client.get_object.assert_called_once_with(Bucket="bucket", Key="key")

    @pytest.mark.unit
    def test_get_object_returns_bytes(self, mock_s3_client):
        """Test that get_object returns bytes type."""
        from src.common.storage_interface import MinIOStorage

        test_data = b"Binary content"
        mock_response = {"Body": io.BytesIO(test_data)}
        mock_s3_client.get_object.return_value = mock_response

        storage = MinIOStorage("http://localhost:9000", "key", "secret")
        result = storage.get_object("bucket", "file.bin")

        assert isinstance(result, bytes)
        assert result == test_data


class TestMinIODeleteObject:
    """Test delete_object operations for MinIO."""

    @pytest.mark.unit
    def test_delete_object(self, mock_s3_client):
        """Test deleting object from MinIO."""
        from src.common.storage_interface import MinIOStorage

        storage = MinIOStorage("http://localhost:9000", "key", "secret")

        storage.delete_object("bucket", "to-delete")

        mock_s3_client.delete_object.assert_called_once_with(Bucket="bucket", Key="to-delete")


class TestMinIOListObjects:
    """Test list_objects operations for MinIO."""

    @pytest.mark.unit
    def test_list_objects(self, mock_s3_client):
        """Test listing objects in MinIO bucket."""
        from src.common.storage_interface import MinIOStorage

        mock_response = {"Contents": [{"Key": "file1.txt"}, {"Key": "file2.txt"}]}
        mock_s3_client.list_objects_v2.return_value = mock_response

        storage = MinIOStorage("http://localhost:9000", "key", "secret")
        result = storage.list_objects("bucket")

        assert result == ["file1.txt", "file2.txt"]
        mock_s3_client.list_objects_v2.assert_called_once_with(Bucket="bucket", Prefix="")

    @pytest.mark.unit
    def test_list_objects_with_prefix(self, mock_s3_client):
        """Test listing objects with prefix."""
        from src.common.storage_interface import MinIOStorage

        mock_response = {"Contents": [{"Key": "logs/app.log"}, {"Key": "logs/error.log"}]}
        mock_s3_client.list_objects_v2.return_value = mock_response

        storage = MinIOStorage("http://localhost:9000", "key", "secret")
        result = storage.list_objects("bucket", prefix="logs/")

        assert result == ["logs/app.log", "logs/error.log"]
        mock_s3_client.list_objects_v2.assert_called_once_with(Bucket="bucket", Prefix="logs/")

    @pytest.mark.unit
    def test_list_objects_empty_bucket(self, mock_s3_client):
        """Test listing objects in empty bucket."""
        from src.common.storage_interface import MinIOStorage

        mock_response = {}  # No Contents key when bucket is empty
        mock_s3_client.list_objects_v2.return_value = mock_response

        storage = MinIOStorage("http://localhost:9000", "key", "secret")
        result = storage.list_objects("bucket")

        assert result == []


class TestStorageBackendFactory:
    """Test storage backend factory function."""

    @pytest.mark.unit
    def test_get_development_backend(self, tmp_path):
        """Test getting development storage backend."""
        from src.common.storage_interface import LocalFilesystemStorage, get_storage_backend

        storage = get_storage_backend("development", base_path=str(tmp_path))

        assert isinstance(storage, LocalFilesystemStorage)
        assert storage.base_path == tmp_path

    @pytest.mark.unit
    def test_get_development_backend_default_path(self):
        """Test development backend uses default path."""
        from src.common.storage_interface import LocalFilesystemStorage, get_storage_backend

        storage = get_storage_backend("development")

        assert isinstance(storage, LocalFilesystemStorage)
        assert "storage" in str(storage.base_path)

    @pytest.mark.unit
    def test_get_testing_backend(self):
        """Test getting testing storage backend (MinIO)."""
        from src.common.storage_interface import MinIOStorage, get_storage_backend

        with patch("boto3.client"):
            storage = get_storage_backend("testing")
            assert isinstance(storage, MinIOStorage)

    @pytest.mark.unit
    def test_get_testing_backend_custom_config(self):
        """Test testing backend with custom MinIO config."""
        from src.common.storage_interface import get_storage_backend

        with patch("boto3.client") as mock_boto:
            storage = get_storage_backend(
                "testing",
                endpoint="http://custom:9001",
                access_key="custom-key",
                secret_key="custom-secret",
            )

            assert storage is not None
            call_kwargs = mock_boto.call_args[1]
            assert call_kwargs["endpoint_url"] == "http://custom:9001"
            assert call_kwargs["aws_access_key_id"] == "custom-key"
            assert call_kwargs["aws_secret_access_key"] == "custom-secret"

    @pytest.mark.unit
    def test_get_production_backend_not_implemented(self):
        """Test that production backend raises NotImplementedError."""
        from src.common.storage_interface import get_storage_backend

        with pytest.raises(NotImplementedError, match="OCI Object Storage"):
            get_storage_backend("production")

    @pytest.mark.unit
    def test_unknown_environment_raises_error(self):
        """Test that unknown environment raises ValueError."""
        from src.common.storage_interface import get_storage_backend

        with pytest.raises(ValueError, match="Unknown environment"):
            get_storage_backend("staging")


class TestStorageIntegration:
    """Test storage operations working together."""

    @pytest.mark.unit
    def test_put_get_delete_workflow_filesystem(self, temp_storage_path):
        """Test complete workflow for filesystem storage."""
        from src.common.storage_interface import LocalFilesystemStorage

        storage = LocalFilesystemStorage(temp_storage_path)
        test_data = b"Workflow test data"

        # Put
        storage.put_object("bucket", "workflow.dat", io.BytesIO(test_data))

        # Get
        retrieved = storage.get_object("bucket", "workflow.dat")
        assert retrieved == test_data

        # List
        objects = storage.list_objects("bucket")
        assert "workflow.dat" in objects

        # Delete
        storage.delete_object("bucket", "workflow.dat")

        # Verify deleted
        with pytest.raises(FileNotFoundError):
            storage.get_object("bucket", "workflow.dat")

    @pytest.mark.unit
    def test_put_get_delete_workflow_minio(self, mock_s3_client):
        """Test complete workflow for MinIO storage."""
        from src.common.storage_interface import MinIOStorage

        test_data = b"MinIO workflow data"
        mock_response = {"Body": io.BytesIO(test_data)}
        mock_s3_client.get_object.return_value = mock_response
        mock_s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "workflow.dat"}]}

        storage = MinIOStorage("http://localhost:9000", "key", "secret")

        # Put
        storage.put_object("bucket", "workflow.dat", io.BytesIO(test_data))
        assert mock_s3_client.put_object.called

        # Get
        retrieved = storage.get_object("bucket", "workflow.dat")
        assert retrieved == test_data

        # List
        objects = storage.list_objects("bucket")
        assert "workflow.dat" in objects

        # Delete
        storage.delete_object("bucket", "workflow.dat")
        assert mock_s3_client.delete_object.called
