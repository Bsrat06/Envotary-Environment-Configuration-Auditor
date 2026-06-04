"""Validators for environment variable security and configuration issues.

This module provides independent validator functions for each diagnostic code
(ENV001-ENV010+). Each validator checks for specific issues and returns findings
without exposing actual environment variable values.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from envsentry.config import SchemaVariable
from envsentry.models import EnvVariable, ParsedEnvFile, ValidationFinding


def check_missing_required(
    env_vars: dict[str, EnvVariable],
    schema: dict[str, SchemaVariable],
) -> list[ValidationFinding]:
    """ENV001: Check for required variables missing from .env file.

    Args:
        env_vars: Dictionary mapping variable names to EnvVariable objects from .env.
        schema: Dictionary mapping variable names to SchemaVariable objects.

    Returns:
        List of ValidationFinding objects for missing required variables.
    """
    findings: list[ValidationFinding] = []

    for var_name, var_schema in schema.items():
        if var_schema.required and var_name not in env_vars:
            findings.append(
                ValidationFinding(
                    code="ENV001",
                    severity="error",
                    variable=var_name,
                    file="(missing)",
                    line=None,
                    message=f"Required variable '{var_name}' is not defined in .env",
                    remediation=f"Add {var_name}=<value> to your .env file",
                )
            )

    return findings


def check_undocumented(
    env_vars: dict[str, EnvVariable],
    schema: dict[str, SchemaVariable],
) -> list[ValidationFinding]:
    """ENV002: Check for variables in .env that are not documented in schema.

    Args:
        env_vars: Dictionary mapping variable names to EnvVariable objects from .env.
        schema: Dictionary mapping variable names to SchemaVariable objects.

    Returns:
        List of ValidationFinding objects for undocumented variables.
    """
    findings: list[ValidationFinding] = []

    for var_name, env_var in env_vars.items():
        if var_name not in schema:
            findings.append(
                ValidationFinding(
                    code="ENV002",
                    severity="warning",
                    variable=var_name,
                    file=env_var.file,
                    line=env_var.line_number,
                    message=f"Variable '{var_name}' is not documented in schema",
                    remediation=f"Add '{var_name}' to .envsentry.toml or .env.example, or remove if unused",
                )
            )

    return findings


def check_duplicates(parsed_file: ParsedEnvFile) -> list[ValidationFinding]:
    """ENV003: Check for duplicate variable definitions in a single file.

    Args:
        parsed_file: Parsed .env file containing duplicate tracking.

    Returns:
        List of ValidationFinding objects for duplicate variables.
    """
    findings: list[ValidationFinding] = []

    for var_name, line_numbers in parsed_file.duplicates.items():
        # Report on the first occurrence
        findings.append(
            ValidationFinding(
                code="ENV003",
                severity="error",
                variable=var_name,
                file=parsed_file.path,
                line=line_numbers[0],
                message=f"Variable '{var_name}' is defined {len(line_numbers)} times (lines: {', '.join(map(str, line_numbers))})",
                remediation=f"Remove duplicate definitions of '{var_name}' and keep only one",
            )
        )

    return findings


def check_empty_required(
    env_vars: dict[str, EnvVariable],
    schema: dict[str, SchemaVariable],
) -> list[ValidationFinding]:
    """ENV004: Check for required variables that are defined but empty.

    Args:
        env_vars: Dictionary mapping variable names to EnvVariable objects from .env.
        schema: Dictionary mapping variable names to SchemaVariable objects.

    Returns:
        List of ValidationFinding objects for empty required variables.
    """
    findings: list[ValidationFinding] = []

    for var_name, env_var in env_vars.items():
        var_schema = schema.get(var_name)
        if var_schema and var_schema.required:
            if env_var.value is None or env_var.value.strip() == "":
                findings.append(
                    ValidationFinding(
                        code="ENV004",
                        severity="error",
                        variable=var_name,
                        file=env_var.file,
                        line=env_var.line_number,
                        message=f"Required variable '{var_name}' is empty",
                        remediation=f"Provide a non-empty value for {var_name}",
                    )
                )

    return findings


def check_invalid_types(
    env_vars: dict[str, EnvVariable],
    schema: dict[str, SchemaVariable],
) -> list[ValidationFinding]:
    """ENV005: Check for type constraint violations (integer, float, boolean).

    Accepted boolean values (case-insensitive):
        - true: 'true', '1', 'yes', 'on'
        - false: 'false', '0', 'no', 'off'

    Args:
        env_vars: Dictionary mapping variable names to EnvVariable objects from .env.
        schema: Dictionary mapping variable names to SchemaVariable objects.

    Returns:
        List of ValidationFinding objects for type violations.
    """
    findings: list[ValidationFinding] = []

    for var_name, env_var in env_vars.items():
        var_schema = schema.get(var_name)
        if not var_schema or env_var.value is None:
            continue

        value = env_var.value.strip()
        if not value:
            continue

        expected_type = var_schema.type

        is_valid = True
        error_msg = ""

        if expected_type == "integer":
            try:
                int(value)
            except ValueError:
                is_valid = False
                error_msg = f"Variable '{var_name}' must be an integer"

        elif expected_type == "float":
            try:
                float(value)
            except ValueError:
                is_valid = False
                error_msg = f"Variable '{var_name}' must be a float"

        elif expected_type == "boolean":
            valid_true = {"true", "1", "yes", "on"}
            valid_false = {"false", "0", "no", "off"}
            if value.lower() not in (valid_true | valid_false):
                is_valid = False
                error_msg = f"Variable '{var_name}' must be a boolean (true/false/1/0/yes/no/on/off)"

        if not is_valid:
            findings.append(
                ValidationFinding(
                    code="ENV005",
                    severity="error",
                    variable=var_name,
                    file=env_var.file,
                    line=env_var.line_number,
                    message=error_msg,
                    remediation=f"Ensure {var_name} contains a valid {expected_type} value",
                )
            )

    return findings


def check_invalid_urls(
    env_vars: dict[str, EnvVariable],
    schema: dict[str, SchemaVariable],
) -> list[ValidationFinding]:
    """ENV006: Check for invalid URL syntax (no network requests).

    Args:
        env_vars: Dictionary mapping variable names to EnvVariable objects from .env.
        schema: Dictionary mapping variable names to SchemaVariable objects.

    Returns:
        List of ValidationFinding objects for invalid URLs.
    """
    findings: list[ValidationFinding] = []

    for var_name, env_var in env_vars.items():
        var_schema = schema.get(var_name)
        if not var_schema or var_schema.type != "url":
            continue

        if env_var.value is None:
            continue

        value = env_var.value.strip()
        if not value:
            continue

        # Parse URL - no network request
        try:
            parsed = urlparse(value)
            # Check for valid scheme and netloc (minimum requirements for a URL)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Missing scheme or netloc")
        except Exception:
            findings.append(
                ValidationFinding(
                    code="ENV006",
                    severity="error",
                    variable=var_name,
                    file=env_var.file,
                    line=env_var.line_number,
                    message=f"Variable '{var_name}' has invalid URL syntax",
                    remediation=f"Ensure {var_name} contains a valid URL with scheme and host",
                )
            )

    return findings


def check_invalid_choices(
    env_vars: dict[str, EnvVariable],
    schema: dict[str, SchemaVariable],
) -> list[ValidationFinding]:
    """ENV007: Check for values not in allowed choices list.

    Args:
        env_vars: Dictionary mapping variable names to EnvVariable objects from .env.
        schema: Dictionary mapping variable names to SchemaVariable objects.

    Returns:
        List of ValidationFinding objects for invalid choices.
    """
    findings: list[ValidationFinding] = []

    for var_name, env_var in env_vars.items():
        var_schema = schema.get(var_name)
        if not var_schema or not var_schema.choices:
            continue

        if env_var.value is None:
            continue

        value = env_var.value.strip()
        if value not in var_schema.choices:
            choices_str = ", ".join(repr(c) for c in var_schema.choices)
            findings.append(
                ValidationFinding(
                    code="ENV007",
                    severity="error",
                    variable=var_name,
                    file=env_var.file,
                    line=env_var.line_number,
                    message=f"Variable '{var_name}' value is not in allowed choices",
                    remediation=f"Set {var_name} to one of: {choices_str}",
                )
            )

    return findings


def check_placeholders(
    env_vars: dict[str, EnvVariable],
    schema: dict[str, SchemaVariable],
) -> list[ValidationFinding]:
    """ENV008: Check for placeholder values that should be replaced.

    Detection heuristics:
        - Patterns like 'your-*-here', 'your-*'
        - 'replace-me', 'change-this', 'changeme'
        - 'example-*', 'example'
        - 'placeholder'
        - '<*>' (angle brackets surrounding text)
        - 'xxx', 'yyy', 'zzz' (common test placeholders)

    Args:
        env_vars: Dictionary mapping variable names to EnvVariable objects from .env.
        schema: Dictionary mapping variable names to SchemaVariable objects.

    Returns:
        List of ValidationFinding objects for detected placeholders.
    """
    findings: list[ValidationFinding] = []

    # Placeholder patterns
    placeholder_patterns = [
        r"^your-.*-here$",
        r"^your-.*",
        r"^replace-?me$",
        r"^change-?this$",
        r"^changeme$",
        r"^example-.*",
        r"^example$",
        r"^placeholder$",
        r"^<.+>$",
        r"^xxx$",
        r"^yyy$",
        r"^zzz$",
    ]

    for var_name, env_var in env_vars.items():
        if env_var.value is None:
            continue

        value = env_var.value.strip().lower()
        if not value:
            continue

        # Check against placeholder patterns
        is_placeholder = False
        for pattern in placeholder_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                is_placeholder = True
                break

        if is_placeholder:
            findings.append(
                ValidationFinding(
                    code="ENV008",
                    severity="warning",
                    variable=var_name,
                    file=env_var.file,
                    line=env_var.line_number,
                    message=f"Variable '{var_name}' appears to contain a placeholder value",
                    remediation=f"Replace the placeholder in {var_name} with an actual value",
                )
            )

    return findings


def check_length_constraints(
    env_vars: dict[str, EnvVariable],
    schema: dict[str, SchemaVariable],
) -> list[ValidationFinding]:
    """ENV009: Check for min_length and max_length constraint violations.

    Args:
        env_vars: Dictionary mapping variable names to EnvVariable objects from .env.
        schema: Dictionary mapping variable names to SchemaVariable objects.

    Returns:
        List of ValidationFinding objects for length constraint violations.
    """
    findings: list[ValidationFinding] = []

    for var_name, env_var in env_vars.items():
        var_schema = schema.get(var_name)
        if not var_schema:
            continue

        if env_var.value is None:
            continue

        value = env_var.value
        value_length = len(value)

        # Check min_length
        if var_schema.min_length is not None and value_length < var_schema.min_length:
            findings.append(
                ValidationFinding(
                    code="ENV009",
                    severity="error",
                    variable=var_name,
                    file=env_var.file,
                    line=env_var.line_number,
                    message=f"Variable '{var_name}' is too short (minimum length: {var_schema.min_length})",
                    remediation=f"Ensure {var_name} has at least {var_schema.min_length} characters",
                )
            )

        # Check max_length
        if var_schema.max_length is not None and value_length > var_schema.max_length:
            findings.append(
                ValidationFinding(
                    code="ENV009",
                    severity="error",
                    variable=var_name,
                    file=env_var.file,
                    line=env_var.line_number,
                    message=f"Variable '{var_name}' is too long (maximum length: {var_schema.max_length})",
                    remediation=f"Ensure {var_name} has at most {var_schema.max_length} characters",
                )
            )

    return findings


def check_numeric_constraints(
    env_vars: dict[str, EnvVariable],
    schema: dict[str, SchemaVariable],
) -> list[ValidationFinding]:
    """ENV010: Check for min and max numeric value constraints.

    Args:
        env_vars: Dictionary mapping variable names to EnvVariable objects from .env.
        schema: Dictionary mapping variable names to SchemaVariable objects.

    Returns:
        List of ValidationFinding objects for numeric constraint violations.
    """
    findings: list[ValidationFinding] = []

    for var_name, env_var in env_vars.items():
        var_schema = schema.get(var_name)
        if not var_schema:
            continue

        if env_var.value is None:
            continue

        value = env_var.value.strip()
        if not value:
            continue

        # Only check numeric constraints for numeric types
        if var_schema.type not in ("integer", "float"):
            continue

        # Try to parse as number
        try:
            if var_schema.type == "integer":
                numeric_value = int(value)
            else:
                numeric_value = float(value)
        except ValueError:
            # Type error - will be caught by check_invalid_types
            continue

        # Check min constraint
        if var_schema.min is not None and numeric_value < var_schema.min:
            findings.append(
                ValidationFinding(
                    code="ENV010",
                    severity="error",
                    variable=var_name,
                    file=env_var.file,
                    line=env_var.line_number,
                    message=f"Variable '{var_name}' is below minimum value (min: {var_schema.min})",
                    remediation=f"Ensure {var_name} is at least {var_schema.min}",
                )
            )

        # Check max constraint
        if var_schema.max is not None and numeric_value > var_schema.max:
            findings.append(
                ValidationFinding(
                    code="ENV010",
                    severity="error",
                    variable=var_name,
                    file=env_var.file,
                    line=env_var.line_number,
                    message=f"Variable '{var_name}' exceeds maximum value (max: {var_schema.max})",
                    remediation=f"Ensure {var_name} is at most {var_schema.max}",
                )
            )

    return findings
