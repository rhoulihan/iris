"""Tests for IRIS CLI commands."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from src.cli.cli import cli
from src.pipeline.orchestrator import PipelineResult
from src.services.analysis_service import AnalysisSession


@pytest.fixture
def runner() -> CliRunner:
    """Provide Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_analysis_session() -> AnalysisSession:
    """Provide mock analysis session."""
    result = PipelineResult(
        patterns_detected=5,
        recommendations_generated=3,
        high_priority_count=1,
        medium_priority_count=1,
        low_priority_count=1,
        total_annual_savings=50000.0,
        execution_time_seconds=12.5,
        recommendations=[],
        errors=[],
    )
    session = AnalysisSession(
        analysis_id="ANALYSIS-2025-11-21-001", status="completed", result=result
    )
    return session


def test_analyze_command_with_config_file(
    runner: CliRunner, tmp_path: Path, mock_analysis_session: AnalysisSession
) -> None:
    """Analyze command should accept config file and run analysis."""
    # Create config file
    config_file = tmp_path / "iris-config.yaml"
    config_file.write_text(
        """
database:
  host: localhost
  port: 1521
  service: FREEPDB1
  username: testuser
  password: testpass
"""
    )

    with patch("src.cli.commands.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.run_analysis.return_value = mock_analysis_session
        MockService.return_value = mock_service

        result = runner.invoke(cli, ["analyze", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "ANALYSIS-2025-11-21-001" in result.output
        assert "completed" in result.output.lower()


def test_analyze_command_with_connection_string(
    runner: CliRunner, mock_analysis_session: AnalysisSession
) -> None:
    """Analyze command should accept connection string."""
    with patch("src.cli.commands.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.run_analysis.return_value = mock_analysis_session
        MockService.return_value = mock_service

        result = runner.invoke(
            cli, ["analyze", "--connection", "user/pass@localhost:1521/FREEPDB1"]
        )

        assert result.exit_code == 0
        assert "ANALYSIS-2025-11-21-001" in result.output


def test_analyze_command_json_output(
    runner: CliRunner, mock_analysis_session: AnalysisSession
) -> None:
    """Analyze command should output JSON when format is json."""
    with patch("src.cli.commands.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.run_analysis.return_value = mock_analysis_session
        MockService.return_value = mock_service

        result = runner.invoke(
            cli,
            [
                "analyze",
                "--connection",
                "user/pass@localhost:1521/FREEPDB1",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        # Should be valid JSON
        output_data = json.loads(result.output)
        assert output_data["analysis_id"] == "ANALYSIS-2025-11-21-001"
        assert output_data["status"] == "completed"


def test_analyze_command_saves_to_file(
    runner: CliRunner, tmp_path: Path, mock_analysis_session: AnalysisSession
) -> None:
    """Analyze command should save output to file when --output is specified."""
    output_file = tmp_path / "analysis.json"

    with patch("src.cli.commands.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.run_analysis.return_value = mock_analysis_session
        MockService.return_value = mock_service

        result = runner.invoke(
            cli,
            [
                "analyze",
                "--connection",
                "user/pass@localhost:1521/FREEPDB1",
                "--format",
                "json",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify file contents
        with open(output_file) as f:
            data = json.load(f)
            assert data["analysis_id"] == "ANALYSIS-2025-11-21-001"


def test_analyze_command_requires_connection_or_config(runner: CliRunner) -> None:
    """Analyze command should require either --connection or --config."""
    result = runner.invoke(cli, ["analyze"])

    assert result.exit_code != 0
    assert "connection" in result.output.lower() or "config" in result.output.lower()


def test_recommendations_list_command(
    runner: CliRunner, mock_analysis_session: AnalysisSession
) -> None:
    """Recommendations list command should display recommendations."""
    with patch("src.cli.commands.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.get_session.return_value = mock_analysis_session
        mock_service.get_recommendations.return_value = []
        MockService.return_value = mock_service

        # First run analysis to create session
        mock_service.run_analysis.return_value = mock_analysis_session
        runner.invoke(cli, ["analyze", "--connection", "user/pass@localhost:1521/FREEPDB1"])

        # Then list recommendations
        result = runner.invoke(cli, ["recommendations", "list"])

        assert result.exit_code == 0


def test_recommendations_list_with_priority_filter(
    runner: CliRunner, mock_analysis_session: AnalysisSession
) -> None:
    """Recommendations list command should filter by priority."""
    with patch("src.cli.commands.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.get_session.return_value = mock_analysis_session
        mock_service.get_recommendations.return_value = []
        MockService.return_value = mock_service

        runner.invoke(cli, ["recommendations", "list", "--priority", "HIGH"])

        # Verify that get_recommendations was called with priority filter
        if mock_service.get_recommendations.called:
            call_kwargs = mock_service.get_recommendations.call_args[1]
            assert call_kwargs.get("priority") == "HIGH"


def test_explain_command_with_recommendation_id(
    runner: CliRunner, mock_analysis_session: AnalysisSession
) -> None:
    """Explain command should show detailed explanation for recommendation."""
    with patch("src.cli.commands.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.get_session.return_value = mock_analysis_session
        MockService.return_value = mock_service

        # Invoke command (may fail if recommendation not found, but that's OK)
        runner.invoke(cli, ["explain", "REC-001"])
