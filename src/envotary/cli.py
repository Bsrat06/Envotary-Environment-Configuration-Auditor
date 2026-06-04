"""CLI interface for Envotary using Typer.

This module provides the command-line interface for Envotary,
including scan and init commands.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from envotary.engine import run_audit
from envotary.exit_codes import EXIT_AUDIT_FAILED, EXIT_ERROR, EXIT_SUCCESS
from envotary.reporters.json import JSONReporter
from envotary.reporters.terminal import TerminalReporter

app = typer.Typer(
    name="envotary",
    help="Security-focused environment variable auditing tool",
    add_completion=False,
)

console = Console()


@app.command()
def scan(
    path: Path = typer.Option(
        Path("."),
        "--path",
        "-p",
        help="Path to the project directory to scan",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    env_file: str | None = typer.Option(
        None,
        "--env-file",
        "-e",
        help="Explicit path to .env file (relative to project path or absolute)",
    ),
    format: str = typer.Option(
        "terminal",
        "--format",
        "-f",
        help="Output format: 'terminal' for human-readable or 'json' for machine-readable",
        case_sensitive=False,
    ),
) -> None:
    """Scan a project for environment variable security issues.

    This command audits your project's .env file against best practices,
    checking for missing required variables, undocumented variables,
    placeholder values, type mismatches, and other security concerns.

    Examples:

        # Scan current directory with terminal output
        envotary scan

        # Scan specific directory with JSON output
        envotary scan --path /path/to/project --format json

        # Use specific .env file
        envotary scan --env-file .env.production
    """
    # Validate format option
    format_lower = format.lower()
    if format_lower not in ("terminal", "json"):
        console.print(
            f"[red]Error:[/red] Invalid format '{format}'. Must be 'terminal' or 'json'.",
        )
        raise typer.Exit(code=EXIT_ERROR)

    try:
        # Run the audit
        audit_result = run_audit(
            project_path=path,
            env_file=env_file,
        )

        # Select and use appropriate reporter
        if format_lower == "json":
            json_reporter = JSONReporter()
            output = json_reporter.report(audit_result)
            # Use print() to avoid Rich formatting for JSON
            print(output)
        else:
            term_reporter = TerminalReporter()
            term_reporter.report(audit_result)

        # Determine exit code based on findings
        error_count = audit_result.summary.get("error", 0)
        if error_count > 0:
            raise typer.Exit(code=EXIT_AUDIT_FAILED)
        else:
            raise typer.Exit(code=EXIT_SUCCESS)

    except typer.Exit:
        # Re-raise typer exits (these are intentional)
        raise
    except Exception as e:
        # Handle unexpected errors
        console.print(
            f"[red]Error:[/red] Execution failed: {e}",
        )
        raise typer.Exit(code=EXIT_ERROR) from e


@app.command()
def init(
    path: Path = typer.Option(
        Path("."),
        "--path",
        "-p",
        help="Path to the project directory",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Initialize Envotary configuration with a starter .envotary.toml file.

    This command creates a .envotary.toml configuration file with helpful
    comments and example variable schemas to get you started quickly.

    The configuration file will not be created if one already exists.

    Example:

        # Create config in current directory
        envotary init

        # Create config in specific directory
        envotary init --path /path/to/project
    """
    config_path = path / ".envotary.toml"

    # Check if config already exists
    if config_path.exists():
        console.print(
            f"[yellow]Warning:[/yellow] Configuration file already exists at {config_path}",
        )
        console.print(
            "[dim]Refusing to overwrite existing configuration.[/dim]",
        )
        raise typer.Exit(code=EXIT_ERROR)

    # Create starter configuration
    starter_config = '''# Envotary Configuration File
# This file defines the schema for your environment variables,
# specifying which variables are required, their types, and validation rules.

# Example variable schema:
# [variables.DATABASE_URL]
# required = true
# type = "url"
# description = "PostgreSQL database connection string"
#
# [variables.API_KEY]
# required = true
# type = "string"
# min_length = 32
# description = "Third-party API authentication key"
#
# [variables.LOG_LEVEL]
# required = false
# type = "choice"
# choices = ["DEBUG", "INFO", "WARNING", "ERROR"]
# description = "Application logging level"
#
# [variables.MAX_CONNECTIONS]
# required = false
# type = "integer"
# min = 1
# max = 100
# description = "Maximum number of concurrent connections"

# Define your environment variables below:

# [variables.YOUR_VARIABLE_NAME]
# required = true
# type = "string"
# description = "Description of what this variable does"
'''

    try:
        config_path.write_text(starter_config, encoding="utf-8")
        console.print(f"[green]✓[/green] Created configuration file: {config_path}")
        console.print()
        console.print("[dim]Next steps:[/dim]")
        console.print("  1. Edit .envotary.toml to define your variable schemas")
        console.print("  2. Run 'envotary scan' to audit your project")
        raise typer.Exit(code=EXIT_SUCCESS)
    except typer.Exit:
        # Re-raise typer exits (these are intentional)
        raise
    except Exception as e:
        console.print(
            f"[red]Error:[/red] Failed to create configuration file: {e}",
        )
        raise typer.Exit(code=EXIT_ERROR) from e


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
