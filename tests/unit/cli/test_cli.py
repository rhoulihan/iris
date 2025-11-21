"""Tests for IRIS CLI entry point."""

from click.testing import CliRunner

from src.cli.cli import cli


def test_cli_without_command_shows_help() -> None:
    """Running 'iris' without command should show usage message."""
    runner = CliRunner()
    result = runner.invoke(cli, [])

    # Click groups exit with code 2 when no command provided (expected behavior)
    assert result.exit_code in (0, 2)
    assert "Usage:" in result.output


def test_cli_help_flag() -> None:
    """Running 'iris --help' should show help message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "IRIS" in result.output
    assert "Commands:" in result.output


def test_cli_version_command() -> None:
    """Running 'iris version' should show version information."""
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])

    assert result.exit_code == 0
    assert "IRIS" in result.output
    assert "1.0.0" in result.output


def test_cli_version_command_verbose() -> None:
    """Running 'iris version --verbose' should show detailed version info."""
    runner = CliRunner()
    result = runner.invoke(cli, ["version", "--verbose"])

    assert result.exit_code == 0
    assert "IRIS" in result.output
    assert "Pipeline" in result.output
    assert "Pattern Detectors" in result.output
    assert "Python" in result.output


def test_cli_version_command_json() -> None:
    """Running 'iris version --format json' should output JSON."""
    runner = CliRunner()
    result = runner.invoke(cli, ["version", "--format", "json"])

    assert result.exit_code == 0
    # Should be valid JSON
    import json

    data = json.loads(result.output)
    assert "version" in data
    assert data["version"] == "1.0.0"
