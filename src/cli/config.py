"""IRIS CLI configuration management."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml  # type: ignore[import-untyped]


class ConfigError(Exception):
    """Configuration validation or loading error."""

    pass


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str = "localhost"
    port: int = 1521
    service: str = "FREEPDB1"
    username: str = "iris_user"
    password: Optional[str] = None


@dataclass
class AnalysisConfig:
    """Analysis configuration."""

    _min_confidence: float = field(default=0.6, init=False, repr=False)
    _detectors: List[str] = field(default_factory=list, init=False, repr=False)
    create_snapshot: bool = True

    VALID_DETECTORS = {
        "LOB_CLIFF",
        "JOIN_DIMENSION",
        "DOCUMENT_RELATIONAL",
        "DUALITY_VIEW",
    }

    def __post_init__(self) -> None:
        """Initialize with defaults."""
        self._min_confidence = 0.6
        self._detectors = [
            "LOB_CLIFF",
            "JOIN_DIMENSION",
            "DOCUMENT_RELATIONAL",
            "DUALITY_VIEW",
        ]

    @property
    def min_confidence(self) -> float:
        """Get min_confidence."""
        return self._min_confidence

    @min_confidence.setter
    def min_confidence(self, value: float) -> None:
        """Set min_confidence with validation."""
        if not 0.0 <= value <= 1.0:
            raise ConfigError(f"min_confidence must be between 0.0 and 1.0, got {value}")
        self._min_confidence = value

    @property
    def detectors(self) -> List[str]:
        """Get detectors."""
        return self._detectors

    @detectors.setter
    def detectors(self, value: List[str]) -> None:
        """Set detectors with validation."""
        for detector in value:
            if detector not in self.VALID_DETECTORS:
                raise ConfigError(
                    f"Invalid detector '{detector}'. Valid detectors: {', '.join(self.VALID_DETECTORS)}"
                )
        self._detectors = value


@dataclass
class OutputConfig:
    """Output configuration."""

    _format: str = field(default="json", init=False, repr=False)
    directory: str = "./iris-reports"

    VALID_FORMATS = {"json", "yaml", "text", "csv"}

    def __post_init__(self) -> None:
        """Initialize with defaults."""
        self._format = "json"

    @property
    def format(self) -> str:
        """Get format."""
        return self._format

    @format.setter
    def format(self, value: str) -> None:
        """Set format with validation."""
        if value not in self.VALID_FORMATS:
            raise ConfigError(
                f"Invalid output format '{value}'. Valid formats: {', '.join(self.VALID_FORMATS)}"
            )
        self._format = value


@dataclass
class SafetyConfig:
    """Safety configuration."""

    require_confirmation: bool = True
    create_backup: bool = True
    dry_run_first: bool = True


@dataclass
class APIConfig:
    """API server configuration."""

    host: str = "0.0.0.0"  # nosec B104 - API server needs to bind to all interfaces
    port: int = 8000
    api_key: Optional[str] = None
    enable_auth: bool = True
    rate_limit: int = 100  # requests per minute


@dataclass
class Config:
    """IRIS configuration."""

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    api: APIConfig = field(default_factory=APIConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Config instance
        """
        config = cls()

        # Database config
        if "database" in data:
            db_data = data["database"]
            config.database = DatabaseConfig(
                host=db_data.get("host", config.database.host),
                port=db_data.get("port", config.database.port),
                service=db_data.get("service", config.database.service),
                username=db_data.get("username", config.database.username),
                password=db_data.get("password", config.database.password),
            )

        # Analysis config
        if "analysis" in data:
            analysis_data = data["analysis"]
            analysis = AnalysisConfig(
                create_snapshot=analysis_data.get(
                    "create_snapshot", config.analysis.create_snapshot
                ),
            )
            # Set validated properties
            if "min_confidence" in analysis_data:
                analysis.min_confidence = analysis_data["min_confidence"]
            if "detectors" in analysis_data:
                analysis.detectors = analysis_data["detectors"]
            config.analysis = analysis

        # Output config
        if "output" in data:
            output_data = data["output"]
            output = OutputConfig(
                directory=output_data.get("directory", config.output.directory),
            )
            # Set validated property
            if "format" in output_data:
                output.format = output_data["format"]
            config.output = output

        # Safety config
        if "safety" in data:
            safety_data = data["safety"]
            config.safety = SafetyConfig(
                require_confirmation=safety_data.get(
                    "require_confirmation", config.safety.require_confirmation
                ),
                create_backup=safety_data.get("create_backup", config.safety.create_backup),
                dry_run_first=safety_data.get("dry_run_first", config.safety.dry_run_first),
            )

        # API config
        if "api" in data:
            api_data = data["api"]
            config.api = APIConfig(
                host=api_data.get("host", config.api.host),
                port=api_data.get("port", config.api.port),
                api_key=api_data.get("api_key", config.api.api_key),
                enable_auth=api_data.get("enable_auth", config.api.enable_auth),
                rate_limit=api_data.get("rate_limit", config.api.rate_limit),
            )

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "service": self.database.service,
                "username": self.database.username,
                "password": self.database.password,
            },
            "analysis": {
                "min_confidence": self.analysis.min_confidence,
                "detectors": self.analysis.detectors,
                "create_snapshot": self.analysis.create_snapshot,
            },
            "output": {
                "format": self.output.format,
                "directory": self.output.directory,
            },
            "safety": {
                "require_confirmation": self.safety.require_confirmation,
                "create_backup": self.safety.create_backup,
                "dry_run_first": self.safety.dry_run_first,
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "api_key": self.api.api_key,
                "enable_auth": self.api.enable_auth,
                "rate_limit": self.api.rate_limit,
            },
        }


def _substitute_env_vars(data: Any) -> Any:
    """Recursively substitute environment variables in configuration data.

    Supports ${VAR_NAME} syntax.

    Args:
        data: Configuration data (dict, list, or string)

    Returns:
        Data with environment variables substituted
    """
    if isinstance(data, dict):
        return {key: _substitute_env_vars(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Match ${VAR_NAME} pattern
        pattern = r"\$\{([^}]+)\}"
        matches = re.findall(pattern, data)
        for var_name in matches:
            env_value = os.environ.get(var_name)
            if env_value is not None:
                data = data.replace(f"${{{var_name}}}", env_value)
        return data
    else:
        return data


def load_config(config_path: str) -> Config:
    """Load configuration from YAML file.

    Supports environment variable substitution using ${VAR_NAME} syntax.

    Args:
        config_path: Path to configuration file

    Returns:
        Config instance

    Raises:
        ConfigError: If file not found or invalid
    """
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(path) as f:
            data = yaml.safe_load(f)

        # Substitute environment variables
        data = _substitute_env_vars(data)

        return Config.from_dict(data)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in configuration file: {e}")
    except Exception as e:
        raise ConfigError(f"Error loading configuration: {e}")


def save_config(config: Config, config_path: str) -> None:
    """Save configuration to YAML file.

    Args:
        config: Config instance to save
        config_path: Path to save configuration file

    Raises:
        ConfigError: If unable to save file
    """
    try:
        data = config.to_dict()
        path = Path(config_path)

        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise ConfigError(f"Error saving configuration: {e}")
