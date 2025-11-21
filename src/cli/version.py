"""IRIS CLI version information."""

import sys
from typing import Any, Dict

# IRIS version (semantic versioning)
__version__ = "1.0.0"


def get_version() -> str:
    """Get IRIS version string.

    Returns:
        Version string in semantic versioning format (X.Y.Z)
    """
    return __version__


def get_version_info() -> Dict[str, Any]:
    """Get detailed version information.

    Returns:
        Dictionary containing:
        - version: IRIS version
        - pipeline_version: Pipeline version
        - pattern_detectors: Number of pattern detectors
        - python_version: Python version
        - oracle_driver: Oracle driver version
    """
    try:
        import oracledb

        oracle_driver = f"oracledb {oracledb.__version__}"
    except (ImportError, AttributeError):
        oracle_driver = "oracledb (not installed)"

    return {
        "version": __version__,
        "pipeline_version": __version__,
        "pattern_detectors": 4,  # LOB, Join, Document, Duality View
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "oracle_driver": oracle_driver,
    }
