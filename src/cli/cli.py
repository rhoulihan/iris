"""IRIS CLI entry point and command definitions."""

import json

import click

from src.cli.version import get_version, get_version_info


@click.group()
@click.version_option(version=get_version(), prog_name="IRIS")
def cli() -> None:
    """IRIS - Intelligent Recommendation and Inference System.

    Oracle Database schema optimization powered by AI.
    """
    pass


@cli.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed version information",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def version(verbose: bool, format: str) -> None:
    """Show IRIS version information."""
    if format == "json":
        # JSON output
        info = get_version_info()
        click.echo(json.dumps(info, indent=2))
    elif verbose:
        # Verbose text output
        info = get_version_info()
        click.echo(f"IRIS v{info['version']}")
        click.echo(f"Pipeline: v{info['pipeline_version']}")
        click.echo(f"Pattern Detectors: {info['pattern_detectors']}")
        click.echo(f"Python: {info['python_version']}")
        click.echo(f"Oracle Driver: {info['oracle_driver']}")
    else:
        # Simple version output
        click.echo(f"IRIS v{get_version()}")


if __name__ == "__main__":
    cli()
