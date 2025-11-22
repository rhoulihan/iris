"""IRIS CLI command implementations."""

import json
import logging
import re
from pathlib import Path
from typing import Optional

import click
import yaml  # type: ignore[import-untyped]

from src.cli.config import DatabaseConfig, load_config
from src.pipeline.orchestrator import PipelineConfig
from src.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

# Global service instance (simplified for CLI usage)
_service: Optional[AnalysisService] = None
_last_analysis_id: Optional[str] = None


def parse_connection_string(conn_str: str) -> DatabaseConfig:
    """Parse Oracle connection string.

    Args:
        conn_str: Connection string in format user/pass@host:port/service

    Returns:
        DatabaseConfig instance

    Raises:
        ValueError: If connection string format is invalid
    """
    pattern = r"^(.+)/(.+)@(.+):(\d+)/(.+)$"
    match = re.match(pattern, conn_str)

    if not match:
        raise ValueError(
            f"Invalid connection string format: {conn_str}. "
            "Expected format: user/pass@host:port/service"
        )

    username, password, host, port, service = match.groups()

    return DatabaseConfig(
        host=host,
        port=int(port),
        service=service,
        username=username,
        password=password,
    )


def format_analysis_output(session, output_format: str) -> str:
    """Format analysis session output.

    Args:
        session: AnalysisSession to format
        output_format: Output format (text, json, yaml)

    Returns:
        Formatted output string
    """
    if output_format == "json":
        data = {
            "analysis_id": session.analysis_id,
            "created_at": session.created_at.isoformat(),
            "status": session.status,
        }

        if session.result:
            data.update(
                {
                    "patterns_detected": session.result.patterns_detected,
                    "recommendations_generated": session.result.recommendations_generated,
                    "high_priority_count": session.result.high_priority_count,
                    "medium_priority_count": session.result.medium_priority_count,
                    "low_priority_count": session.result.low_priority_count,
                    "total_annual_savings": session.result.total_annual_savings,
                    "execution_time_seconds": session.result.execution_time_seconds,
                }
            )

        return json.dumps(data, indent=2)

    elif output_format == "yaml":
        data = {
            "analysis_id": session.analysis_id,
            "status": session.status,
        }
        if session.result:
            data["result"] = {
                "patterns_detected": session.result.patterns_detected,
                "recommendations": session.result.recommendations_generated,
            }
        return str(yaml.dump(data))

    else:  # text format
        output = [
            f"Analysis ID: {session.analysis_id}",
            f"Status: {session.status}",
            f"Created: {session.created_at}",
        ]

        if session.result:
            output.extend(
                [
                    "",
                    "Results:",
                    f"  Patterns detected: {session.result.patterns_detected}",
                    f"  Recommendations: {session.result.recommendations_generated}",
                    f"    - HIGH priority: {session.result.high_priority_count}",
                    f"    - MEDIUM priority: {session.result.medium_priority_count}",
                    f"    - LOW priority: {session.result.low_priority_count}",
                    f"  Estimated annual savings: ${session.result.total_annual_savings:,.2f}",
                    f"  Execution time: {session.result.execution_time_seconds:.2f}s",
                ]
            )

        if session.error:
            output.extend(["", f"Error: {session.error}"])

        return "\n".join(output)


@click.command()
@click.option(
    "--connection",
    "-c",
    help="Database connection string (user/pass@host:port/service)",
)
@click.option("--config", type=click.Path(exists=True), help="Path to configuration file")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: stdout)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "yaml"]),
    default="text",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def analyze(
    connection: Optional[str],
    config: Optional[str],
    output: Optional[str],
    format: str,
    verbose: bool,
) -> None:
    """Run analysis on Oracle database."""
    global _service, _last_analysis_id

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Validate inputs
    if not connection and not config:
        raise click.UsageError("Either --connection or --config must be provided")

    try:
        # Load configuration
        if config:
            full_config = load_config(config)
            db_config = full_config.database
            pipeline_config = PipelineConfig(
                min_confidence_threshold=full_config.analysis.min_confidence,
            )
        else:
            db_config = parse_connection_string(connection)  # type: ignore
            pipeline_config = PipelineConfig()

        # Create service and run analysis
        _service = AnalysisService(db_config, pipeline_config)
        session = _service.run_analysis()
        _last_analysis_id = session.analysis_id

        # Format output
        output_text = format_analysis_output(session, format)

        # Write to file or stdout
        if output:
            Path(output).write_text(output_text)
            click.echo(f"Analysis results saved to {output}")
        else:
            click.echo(output_text)

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise click.ClickException(str(e))


@click.group()
def recommendations() -> None:
    """Manage and view recommendations."""
    pass


@recommendations.command("list")
@click.option("--priority", type=click.Choice(["HIGH", "MEDIUM", "LOW"]), help="Filter by priority")
@click.option("--pattern-type", help="Filter by pattern type")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def recommendations_list(priority: Optional[str], pattern_type: Optional[str], format: str) -> None:
    """List all recommendations from last analysis."""
    global _service, _last_analysis_id

    if not _service or not _last_analysis_id:
        raise click.ClickException("No analysis has been run. Run 'iris analyze' first.")

    try:
        recs = _service.get_recommendations(
            _last_analysis_id, priority=priority, pattern_type=pattern_type
        )

        if format == "json":
            data = [
                {
                    "recommendation_id": rec.recommendation_id,
                    "type": rec.type,
                    "priority": rec.priority,
                    "description": rec.description,
                    "annual_savings": rec.annual_savings,
                }
                for rec in recs
            ]
            click.echo(json.dumps(data, indent=2))
        else:
            if not recs:
                click.echo("No recommendations found.")
                return

            click.echo(f"Found {len(recs)} recommendation(s):\n")
            for rec in recs:
                click.echo(f"  [{rec.priority}] {rec.recommendation_id}")
                click.echo(f"    Type: {rec.type}")
                click.echo(f"    Savings: ${rec.annual_savings:,.2f}/year")
                click.echo(f"    {rec.description}\n")

    except Exception as e:
        logger.error(f"Failed to list recommendations: {e}", exc_info=True)
        raise click.ClickException(str(e))


@click.command()
@click.argument("recommendation_id")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "markdown", "json"]),
    default="text",
)
def explain(recommendation_id: str, format: str) -> None:
    """Show detailed explanation for a recommendation."""
    global _service, _last_analysis_id

    if not _service or not _last_analysis_id:
        raise click.ClickException("No analysis has been run. Run 'iris analyze' first.")

    try:
        rec = _service.get_recommendation(_last_analysis_id, recommendation_id)

        if format == "json":
            data = {
                "recommendation_id": rec.recommendation_id,
                "type": rec.type,
                "priority": rec.priority,
                "description": rec.description,
                "rationale": {
                    "pattern_detected": rec.rationale.pattern_detected,
                    "current_cost": rec.rationale.current_cost,
                    "expected_benefit": rec.rationale.expected_benefit,
                },
                "implementation": {
                    "sql": rec.implementation.sql,
                    "rollback_plan": rec.implementation.rollback_plan,
                    "testing_approach": rec.implementation.testing_approach,
                },
                "estimated_improvement_pct": rec.estimated_improvement_pct,
                "annual_savings": rec.annual_savings,
                "roi_percentage": rec.roi_percentage,
            }
            click.echo(json.dumps(data, indent=2))

        else:  # text or markdown
            sep = "=" * 60 if format == "text" else "---"

            output = [
                f"Recommendation: {rec.recommendation_id}",
                f"Type: {rec.type}",
                f"Priority: {rec.priority}",
                "",
                sep,
                "",
                "RATIONALE",
                f"Pattern Detected: {rec.rationale.pattern_detected}",
                f"Current Cost: {rec.rationale.current_cost}",
                f"Expected Benefit: {rec.rationale.expected_benefit}",
                "",
                sep,
                "",
                "IMPACT ANALYSIS",
                f"Estimated Improvement: {rec.estimated_improvement_pct}%",
                f"Annual Savings: ${rec.annual_savings:,.2f}",
                f"ROI: {rec.roi_percentage}%",
                "",
                sep,
                "",
                "IMPLEMENTATION",
                "SQL:",
                rec.implementation.sql,
                "",
                "Rollback Plan:",
                rec.implementation.rollback_plan,
                "",
                "Testing Approach:",
                rec.implementation.testing_approach,
            ]

            click.echo("\n".join(output))

    except ValueError as e:
        raise click.ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to explain recommendation: {e}", exc_info=True)
        raise click.ClickException(str(e))
