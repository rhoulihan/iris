"""Tests for IRIS CLI version information."""

from src.cli.version import get_version, get_version_info


def test_get_version_returns_string() -> None:
    """get_version should return a version string."""
    version = get_version()

    assert isinstance(version, str)
    assert len(version) > 0


def test_get_version_follows_semver() -> None:
    """Version should follow semantic versioning (X.Y.Z)."""
    version = get_version()

    parts = version.split(".")
    assert len(parts) == 3

    # Each part should be a number
    for part in parts:
        assert part.isdigit()


def test_get_version_info_returns_dict() -> None:
    """get_version_info should return a dictionary with version details."""
    info = get_version_info()

    assert isinstance(info, dict)
    assert "version" in info
    assert "pipeline_version" in info
    assert "pattern_detectors" in info


def test_get_version_info_includes_pattern_detector_count() -> None:
    """Version info should include count of pattern detectors."""
    info = get_version_info()

    assert "pattern_detectors" in info
    detectors = info["pattern_detectors"]

    assert isinstance(detectors, int)
    assert detectors == 4  # LOB, Join, Document, Duality View


def test_get_version_info_includes_python_version() -> None:
    """Version info should include Python version."""
    info = get_version_info()

    assert "python_version" in info
    assert isinstance(info["python_version"], str)
    assert len(info["python_version"]) > 0


def test_get_version_info_includes_oracle_driver() -> None:
    """Version info should include Oracle driver version."""
    info = get_version_info()

    assert "oracle_driver" in info
    assert isinstance(info["oracle_driver"], str)
    assert "oracledb" in info["oracle_driver"]
