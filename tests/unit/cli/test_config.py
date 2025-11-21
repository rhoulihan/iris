"""Tests for IRIS CLI configuration management."""

from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from src.cli.config import Config, ConfigError, load_config, save_config


def test_config_creation_with_defaults() -> None:
    """Config should be created with sensible defaults."""
    config = Config()

    assert config.analysis.min_confidence == 0.6
    assert "LOB_CLIFF" in config.analysis.detectors
    assert len(config.analysis.detectors) == 4
    assert config.safety.require_confirmation is True
    assert config.output.format == "json"


def test_config_from_dict() -> None:
    """Config should be created from dictionary."""
    data: Dict[str, Any] = {
        "database": {
            "host": "testhost",
            "port": 1521,
            "service": "TESTDB",
            "username": "testuser",
        },
        "analysis": {
            "min_confidence": 0.8,
        },
    }

    config = Config.from_dict(data)

    assert config.database.host == "testhost"
    assert config.database.port == 1521
    assert config.database.service == "TESTDB"
    assert config.analysis.min_confidence == 0.8


def test_config_to_dict() -> None:
    """Config should be converted to dictionary."""
    config = Config()
    config.database.host = "myhost"
    config.database.port = 1524

    data = config.to_dict()

    assert isinstance(data, dict)
    assert data["database"]["host"] == "myhost"
    assert data["database"]["port"] == 1524


def test_config_validates_min_confidence() -> None:
    """Config should validate min_confidence is between 0 and 1."""
    with pytest.raises(ConfigError, match="min_confidence"):
        config = Config()
        config.analysis.min_confidence = 1.5


def test_load_config_from_yaml_file(tmp_path: Path) -> None:
    """load_config should load configuration from YAML file."""
    config_file = tmp_path / "iris-config.yaml"
    config_data = {
        "database": {
            "host": "yamlhost",
            "port": 1525,
            "service": "YAMLDB",
        },
        "analysis": {
            "min_confidence": 0.75,
        },
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = load_config(str(config_file))

    assert config.database.host == "yamlhost"
    assert config.database.port == 1525
    assert config.analysis.min_confidence == 0.75


def test_load_config_with_env_vars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """load_config should substitute environment variables."""
    config_file = tmp_path / "iris-config.yaml"
    config_data = {
        "database": {
            "host": "${DB_HOST}",
            "port": 1521,
            "username": "${DB_USER}",
            "password": "${DB_PASS}",
        },
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Set environment variables
    monkeypatch.setenv("DB_HOST", "env-host")
    monkeypatch.setenv("DB_USER", "env-user")
    monkeypatch.setenv("DB_PASS", "env-pass")

    config = load_config(str(config_file))

    assert config.database.host == "env-host"
    assert config.database.username == "env-user"
    assert config.database.password == "env-pass"


def test_load_config_nonexistent_file() -> None:
    """load_config should raise error for nonexistent file."""
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/config.yaml")


def test_save_config_to_yaml(tmp_path: Path) -> None:
    """save_config should save configuration to YAML file."""
    config = Config()
    config.database.host = "savehost"
    config.database.port = 1526
    config.analysis.min_confidence = 0.9

    config_file = tmp_path / "saved-config.yaml"
    save_config(config, str(config_file))

    # Verify file was created and contains correct data
    assert config_file.exists()

    with open(config_file) as f:
        data = yaml.safe_load(f)

    assert data["database"]["host"] == "savehost"
    assert data["database"]["port"] == 1526
    assert data["analysis"]["min_confidence"] == 0.9


def test_config_detectors_validation() -> None:
    """Config should validate detector names."""
    with pytest.raises(ConfigError, match="Invalid detector"):
        config = Config()
        config.analysis.detectors = ["INVALID_DETECTOR"]


def test_config_output_format_validation() -> None:
    """Config should validate output format."""
    with pytest.raises(ConfigError, match="output format"):
        config = Config()
        config.output.format = "invalid"
