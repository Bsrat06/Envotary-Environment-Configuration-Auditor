"""Terminal reporter for EnvSentry using Rich for formatted output.

This module provides a professional, human-readable terminal reporter
that displays audit results with proper formatting and color coding.
"""

from __future__ import annotations
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from envsentry.models import AuditResult, ValidationFinding


class TerminalReporter:
    """Terminal reporter that uses Rich to display audit results.

    This reporter formats audit results for human consumption with:
    - Project header showing scanned path
    - Summary statistics by severity
    - Findings grouped by severity (errors first, then warnings)
    - File:line references, diagnostic codes, and remediation steps
    - Final pass/fail status

    Security: NEVER displays actual environment variable values.
    """

    def __init__(self) -> None:
        """Initialize the terminal reporter with a Rich console."""
        self.console = Console()

    def report(self, audit_result: AuditResult) -> None:
        """Display an audit result to the terminal.

        Args:
            audit_result: The complete audit result to display.
        """
        self._print_header(audit_result.project_path)
        self._print_summary(audit_result.summary)

        if audit_result.findings:
            self._print_findings(audit_result.findings)
        else:
            self.console.print("\n[green]✓ No issues found[/green]\n")

        self._print_footer(audit_result.summary)

    def _print_header(self, project_path: str) -> None:
        """Print the project header.

        Args:
            project_path: Path to the audited project.
        """
        self.console.print()
        self.console.print(
            Panel(
                f"[bold]EnvSentry Security Audit[/bold]\n[dim]Project:[/dim] {project_path}",
                border_style="blue",
            )
        )
        self.console.print()

    def _print_summary(self, summary: dict[str, int]) -> None:
        """Print summary statistics.

        Args:
            summary: Dictionary mapping severity levels to counts.
        """
        error_count = summary.get("error", 0)
        warning_count = summary.get("warning", 0)
        info_count = summary.get("info", 0)

        summary_text = Text()
        summary_text.append("Summary: ", style="bold")

        if error_count > 0:
            summary_text.append(f"{error_count} error(s)", style="bold red")
        else:
            summary_text.append(f"{error_count} error(s)", style="dim")

        summary_text.append(" | ")

        if warning_count > 0:
            summary_text.append(f"{warning_count} warning(s)", style="bold yellow")
        else:
            summary_text.append(f"{warning_count} warning(s)", style="dim")

        if info_count > 0:
            summary_text.append(" | ")
            summary_text.append(f"{info_count} info", style="cyan")

        self.console.print(summary_text)
        self.console.print()

    def _print_findings(self, findings: list[ValidationFinding]) -> None:
        """Print all findings grouped by severity.

        Args:
            findings: List of validation findings to display.
        """
        # Group findings by severity
        errors = [f for f in findings if f.severity == "error"]
        warnings = [f for f in findings if f.severity == "warning"]
        infos = [f for f in findings if f.severity == "info"]

        # Display errors first
        if errors:
            self._print_findings_group("Errors", errors, "red")

        # Then warnings
        if warnings:
            self._print_findings_group("Warnings", warnings, "yellow")

        # Then info
        if infos:
            self._print_findings_group("Information", infos, "cyan")

    def _print_findings_group(
        self,
        group_name: str,
        findings: list[ValidationFinding],
        color: str,
    ) -> None:
        """Print a group of findings with the same severity.

        Args:
            group_name: Display name for this severity group.
            findings: List of findings in this group.
            color: Color to use for the group header.
        """
        self.console.print(f"[bold {color}]{group_name}:[/bold {color}]")
        self.console.print()

        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
        table.add_column("Code", style=color, no_wrap=True)
        table.add_column("Variable", style="cyan")
        table.add_column("Location")
        table.add_column("Issue")

        for finding in findings:
            # Format location
            location = finding.file
            if finding.line is not None:
                location += f":{finding.line}"

            # Format issue (message + remediation)
            issue = finding.message
            if finding.remediation:
                issue += f"\n[dim]→ {finding.remediation}[/dim]"

            table.add_row(
                finding.code,
                finding.variable,
                location,
                issue,
            )

        self.console.print(table)
        self.console.print()

    def _print_footer(self, summary: dict[str, int]) -> None:
        """Print final pass/fail status.

        Args:
            summary: Dictionary mapping severity levels to counts.
        """
        error_count = summary.get("error", 0)

        if error_count > 0:
            self.console.print(
                Panel(
                    f"[bold red]✗ Audit failed with {error_count} error(s)[/bold red]",
                    border_style="red",
                )
            )
        else:
            self.console.print(
                Panel(
                    "[bold green]✓ Audit passed[/bold green]",
                    border_style="green",
                )
            )
        self.console.print()
