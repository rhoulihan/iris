"""Pytest configuration and shared fixtures for IRIS tests.

This module provides common test fixtures and configuration for all test modules.
Fixtures are automatically discovered by pytest across all test files.
"""

import os
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory.

    Returns:
        Path to the project root directory
    """
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """Return the test data directory.

    Returns:
        Path to tests/data directory
    """
    return project_root / "tests" / "data"


@pytest.fixture(scope="session")
def fixtures_dir(test_data_dir: Path) -> Path:
    """Return the test fixtures directory.

    Returns:
        Path to tests/data/fixtures directory
    """
    return test_data_dir / "fixtures"


@pytest.fixture(scope="function")
def temp_storage_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary directory for storage operations.

    This fixture creates a temporary directory that's automatically cleaned up
    after each test.

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Yields:
        Path to temporary storage directory
    """
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    yield storage_dir


@pytest.fixture(scope="session")
def oracle_test_config() -> dict:
    """Provide Oracle database test configuration.

    Returns test database configuration from environment variables or defaults
    for local development.

    Returns:
        Dictionary with Oracle connection parameters
    """
    return {
        "host": os.getenv("ORACLE_HOST", "localhost"),
        "port": int(os.getenv("ORACLE_PORT", "1524")),
        "service_name": os.getenv("ORACLE_SERVICE", "FREEPDB1"),
        "user": os.getenv("ORACLE_USER", "iris_user"),
        "password": os.getenv("ORACLE_PASSWORD", "IrisUser123!"),
    }


@pytest.fixture(scope="session")
def redis_test_config() -> dict:
    """Provide Redis test configuration.

    Returns test Redis configuration from environment variables or defaults
    for local development.

    Returns:
        Dictionary with Redis connection parameters
    """
    return {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": int(os.getenv("REDIS_DB", "0")),
    }


@pytest.fixture(scope="session")
def minio_test_config() -> dict:
    """Provide MinIO test configuration.

    Returns test MinIO configuration from environment variables or defaults
    for local development.

    Returns:
        Dictionary with MinIO connection parameters
    """
    return {
        "endpoint": os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
        "access_key": os.getenv("MINIO_ACCESS_KEY", "iris-admin"),
        "secret_key": os.getenv("MINIO_SECRET_KEY", "IrisMinIO123!"),
    }


# Pytest configuration hooks


def pytest_configure(config):
    """Configure pytest with custom markers.

    Args:
        config: pytest configuration object
    """
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests requiring services")
    config.addinivalue_line("markers", "ml: Machine learning tests")
    config.addinivalue_line("markers", "slow: Tests that take more than 1 second")
    config.addinivalue_line("markers", "oracle: Tests requiring Oracle database connection")
    config.addinivalue_line("markers", "redis: Tests requiring Redis connection")
