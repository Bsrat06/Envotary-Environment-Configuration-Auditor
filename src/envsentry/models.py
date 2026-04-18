"""Data models for EnvSentry.

This module defines the core data structures used throughout the application
for representing parsed environment variables, validation findings, and audit results.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class EnvVariable:
    """Represents a single environment variable extracted from a file.

    Attributes:
        name: The variable name (left side of KEY=value).
        value: The variable value (right side of KEY=value), or None if empty.
        line_number: Line number where this variable was found (1-indexed), or None if unknown.
        file: Path to the file containing this variable.
    """

    name: str
    value: str | None
    line_number: int | None
    file: str


@dataclass
class ParsedEnvFile:
    """Represents a parsed .env file with all extracted variables.

    Attributes:
        path: Absolute path to the parsed file.
        variables: List of all environment variables found in the file.
        duplicates: Dictionary mapping variable names to list of line numbers
                    where duplicates were found. Only includes variables that
                    appear more than once.
    """

    path: str
    variables: list[EnvVariable]
    duplicates: dict[str, list[int]] = field(default_factory=dict)


@dataclass
class ValidationFinding:
    """Represents a single security or configuration issue found during validation.

    Attributes:
        code: Diagnostic code (e.g., 'ENV001', 'ENV002').
        severity: Severity level ('error', 'warning', 'info').
        variable: Name of the environment variable this finding relates to.
        file: Path to the file containing the issue.
        line: Line number where the issue was found (1-indexed), or None if N/A.
        message: Human-readable description of the issue.
        remediation: Suggested fix or action to resolve the issue.
    """

    code: str
    severity: str
    variable: str
    file: str
    line: int | None
    message: str
    remediation: str


@dataclass
class AuditResult:
    """Represents the complete result of an EnvSentry audit run.

    Attributes:
        project_path: Root path of the audited project.
        findings: List of all validation findings discovered.
        summary: Dictionary with counts by severity (e.g., {'error': 2, 'warning': 1}).
    """

    project_path: str
    findings: list[ValidationFinding]
    summary: dict[str, int] = field(default_factory=dict)
