"""Audit engine for EnvSentry.

This module orchestrates the complete audit workflow: file discovery,
parsing, schema loading, validation, and result aggregation.
"""

from __future__ import annotations

from pathlib import Path

from envsentry import validators
from envsentry.config import infer_schema_from_example, load_config
from envsentry.discovery import discover_files
from envsentry.models import AuditResult, ValidationFinding
from envsentry.parser import ParseError, parse_dotenv_file


def run_audit(
    project_path: Path,
    env_file: str | None = None,
    example_file: str | None = None,
    settings: dict | None = None,
) -> AuditResult:
    """Run a complete EnvSentry audit on a project.

    Args:
        project_path: Root directory of the project to audit.
        env_file: Optional explicit path to .env file.
        example_file: Optional explicit path to .env.example file.
        settings: Optional settings dictionary (reserved for future use).

    Returns:
        AuditResult containing all findings and summary statistics.
    """
    if settings is None:
        settings = {}

    findings: list[ValidationFinding] = []
    project_path = project_path.resolve()

    # Step 1: Discover files
    discovered = discover_files(project_path, env_file, example_file)
    env_file_path = discovered["env_file"]
    example_file_path = discovered["example_file"]
    config_file_path = discovered["config_file"]

    # Step 2: Parse .env file
    parsed_env = None
    env_vars = {}
    if env_file_path:
        try:
            parsed_env = parse_dotenv_file(env_file_path)
            # Build a lookup dictionary
            env_vars = {var.name: var for var in parsed_env.variables}
        except FileNotFoundError:
            findings.append(
                ValidationFinding(
                    code="PARSE_ERROR",
                    severity="error",
                    variable="(N/A)",
                    file=str(env_file_path),
                    line=None,
                    message=f".env file not found: {env_file_path}",
                    remediation="Ensure the .env file exists at the specified path",
                )
            )
        except ParseError as e:
            findings.append(
                ValidationFinding(
                    code="PARSE_ERROR",
                    severity="error",
                    variable="(N/A)",
                    file=e.file_path,
                    line=e.line_number,
                    message=f"Failed to parse .env file: {e.message}",
                    remediation="Fix syntax errors in the .env file",
                )
            )
    else:
        # No .env file found
        findings.append(
            ValidationFinding(
                code="ENV_FILE_MISSING",
                severity="warning",
                variable="(N/A)",
                file="(missing)",
                line=None,
                message="No .env file found in project",
                remediation="Create a .env file with required environment variables",
            )
        )

    # Step 3: Parse .env.example file (if exists)
    parsed_example = None
    if example_file_path:
        try:
            parsed_example = parse_dotenv_file(example_file_path)
        except (FileNotFoundError, ParseError):
            # Non-critical - example file is optional
            pass

    # Step 4: Load or infer schema
    schema = {}
    try:
        if config_file_path:
            schema = load_config(config_file_path)
        elif parsed_example:
            schema = infer_schema_from_example(parsed_example)
        # If neither config nor example exists, schema remains empty
    except (FileNotFoundError, ValueError) as e:
        findings.append(
            ValidationFinding(
                code="CONFIG_ERROR",
                severity="error",
                variable="(N/A)",
                file=str(config_file_path) if config_file_path else "(unknown)",
                line=None,
                message=f"Failed to load configuration: {e}",
                remediation="Fix errors in .envsentry.toml or provide a valid .env.example",
            )
        )

    # Step 5: Run all validators (only if we have a valid parsed .env)
    if parsed_env and not any(f.code in ("PARSE_ERROR", "CONFIG_ERROR") for f in findings):
        findings.extend(validators.check_missing_required(env_vars, schema))
        findings.extend(validators.check_undocumented(env_vars, schema))
        findings.extend(validators.check_duplicates(parsed_env))
        findings.extend(validators.check_empty_required(env_vars, schema))
        findings.extend(validators.check_invalid_types(env_vars, schema))
        findings.extend(validators.check_invalid_urls(env_vars, schema))
        findings.extend(validators.check_invalid_choices(env_vars, schema))
        findings.extend(validators.check_placeholders(env_vars, schema))
        findings.extend(validators.check_length_constraints(env_vars, schema))
        findings.extend(validators.check_numeric_constraints(env_vars, schema))

    # Step 6: Generate summary
    summary = {"error": 0, "warning": 0, "info": 0}
    for finding in findings:
        severity = finding.severity
        if severity in summary:
            summary[severity] += 1

    return AuditResult(
        project_path=str(project_path),
        findings=findings,
        summary=summary,
    )
