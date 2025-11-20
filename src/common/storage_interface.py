"""Storage abstraction layer for IRIS project.

Provides unified interface for object storage across different backends:
- Local filesystem (development)
- MinIO (integration testing)
- Oracle Object Storage (production)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class StorageInterface(ABC):
    """Abstract interface for object storage operations."""

    @abstractmethod
    def put_object(self, bucket: str, key: str, data: BinaryIO) -> None:
        """Upload object to storage.

        Args:
            bucket: Bucket or container name
            key: Object key/path
            data: Binary data stream to upload
        """
        pass

    @abstractmethod
    def get_object(self, bucket: str, key: str) -> bytes:
        """Download object from storage.

        Args:
            bucket: Bucket or container name
            key: Object key/path

        Returns:
            Binary content of the object
        """
        pass

    @abstractmethod
    def delete_object(self, bucket: str, key: str) -> None:
        """Delete object from storage.

        Args:
            bucket: Bucket or container name
            key: Object key/path
        """
        pass

    @abstractmethod
    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """List objects with given prefix.

        Args:
            bucket: Bucket or container name
            prefix: Optional prefix filter

        Returns:
            List of object keys matching the prefix
        """
        pass


class LocalFilesystemStorage(StorageInterface):
    """Local filesystem implementation for development."""

    def __init__(self, base_path: Path):
        """Initialize local filesystem storage.

        Args:
            base_path: Base directory for storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def put_object(self, bucket: str, key: str, data: BinaryIO) -> None:
        """Upload object to local filesystem."""
        target_path = self.base_path / bucket / key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(data.read())

    def get_object(self, bucket: str, key: str) -> bytes:
        """Download object from local filesystem."""
        target_path = self.base_path / bucket / key
        with open(target_path, "rb") as f:
            return f.read()

    def delete_object(self, bucket: str, key: str) -> None:
        """Delete object from local filesystem."""
        target_path = self.base_path / bucket / key
        target_path.unlink(missing_ok=True)

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """List objects in local filesystem."""
        bucket_path = self.base_path / bucket
        if not bucket_path.exists():
            return []

        if prefix:
            # Find all files that start with prefix
            results = []
            for item in bucket_path.rglob("*"):
                if item.is_file():
                    rel_path = str(item.relative_to(bucket_path))
                    if rel_path.startswith(prefix):
                        results.append(rel_path)
            return results
        else:
            # Return all files
            return [str(p.relative_to(bucket_path)) for p in bucket_path.rglob("*") if p.is_file()]


class MinIOStorage(StorageInterface):
    """MinIO S3-compatible storage for integration testing."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        """Initialize MinIO storage.

        Args:
            endpoint: MinIO endpoint URL
            access_key: Access key ID
            secret_key: Secret access key
        """
        import boto3
        from botocore.client import Config

        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

    def put_object(self, bucket: str, key: str, data: BinaryIO) -> None:
        """Upload object to MinIO."""
        self.s3.put_object(Bucket=bucket, Key=key, Body=data)

    def get_object(self, bucket: str, key: str) -> bytes:
        """Download object from MinIO."""
        response = self.s3.get_object(Bucket=bucket, Key=key)
        return bytes(response["Body"].read())

    def delete_object(self, bucket: str, key: str) -> None:
        """Delete object from MinIO."""
        self.s3.delete_object(Bucket=bucket, Key=key)

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """List objects in MinIO bucket."""
        response = self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]


def get_storage_backend(env: str = "development", **kwargs) -> StorageInterface:
    """Get appropriate storage backend for the given environment.

    Args:
        env: Environment name (development, testing, production)
        **kwargs: Additional backend-specific configuration

    Returns:
        StorageInterface implementation for the specified environment

    Example:
        >>> storage = get_storage_backend("development")
        >>> with open("model.pth", "rb") as f:
        ...     storage.put_object("models", "v1/model.pth", f)
    """
    if env == "development":
        base_path = kwargs.get("base_path", "./data/storage")
        return LocalFilesystemStorage(Path(base_path))

    elif env == "testing":
        endpoint = kwargs.get("endpoint", "http://localhost:9000")
        access_key = kwargs.get("access_key", "iris-admin")
        secret_key = kwargs.get("secret_key", "IrisMinIO123!")
        return MinIOStorage(endpoint, access_key, secret_key)

    elif env == "production":
        # Oracle Object Storage implementation would go here
        # This requires Oracle Cloud Infrastructure SDK
        raise NotImplementedError("OCI Object Storage not yet implemented")

    else:
        raise ValueError(f"Unknown environment: {env}")
