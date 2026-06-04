"""Dotenv file parser for Envotary.

This module provides functionality to parse .env files and extract environment
variable definitions with line tracking and duplicate detection.

Supported Syntax:
    - Basic KEY=value pairs
    - Single-quoted values: KEY='value'
    - Double-quoted values: KEY="value"
    - Comments starting with #
    - Empty values: KEY= or KEY
    - Values containing = signs
    - Whitespace trimming around keys and values
    - Duplicate key detection with line tracking
"""

from __future__ import annotations

import re
from pathlib import Path

from envotary.models import EnvVariable, ParsedEnvFile


class ParseError(Exception):
    """Exception raised when parsing a .env file fails.

    Attributes:
        file_path: Path to the file that failed to parse.
        line_number: Line number where the error occurred (1-indexed).
        message: Description of what went wrong.
    """

    def __init__(self, file_path: str, line_number: int | None, message: str) -> None:
        self.file_path = file_path
        self.line_number = line_number
        self.message = message
        super().__init__(
            f"Parse error in {file_path}"
            + (f" at line {line_number}" if line_number else "")
            + f": {message}"
        )


def parse_dotenv_file(file_path: Path) -> ParsedEnvFile:
    """Parse a .env file and extract all environment variables.

    Args:
        file_path: Path to the .env file to parse.

    Returns:
        ParsedEnvFile containing all parsed variables and duplicate tracking.

    Raises:
        FileNotFoundError: If the file does not exist.
        ParseError: If the file contains syntax errors that prevent parsing.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ParseError(str(file_path), None, "Path is not a file")

    variables: list[EnvVariable] = []
    duplicates: dict[str, list[int]] = {}
    key_occurrences: dict[str, list[int]] = {}

    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError as e:
        raise ParseError(str(file_path), None, f"File encoding error: {e}")
    except OSError as e:
        raise ParseError(str(file_path), None, f"Failed to read file: {e}")

    for line_num, line in enumerate(lines, start=1):
        # Strip whitespace
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Try to parse KEY=value
        parsed = _parse_line(stripped, line_num)
        if parsed is None:
            # Line is not a valid KEY=value format, skip silently
            # (some .env files may have other content)
            continue

        key, value = parsed

        # Create variable entry
        var = EnvVariable(
            name=key,
            value=value,
            line_number=line_num,
            file=str(file_path.absolute()),
        )
        variables.append(var)

        # Track duplicates
        if key not in key_occurrences:
            key_occurrences[key] = []
        key_occurrences[key].append(line_num)

    # Identify duplicates (keys that appear more than once)
    for key, line_numbers in key_occurrences.items():
        if len(line_numbers) > 1:
            duplicates[key] = line_numbers

    return ParsedEnvFile(
        path=str(file_path.absolute()),
        variables=variables,
        duplicates=duplicates,
    )


def _parse_line(line: str, line_num: int) -> tuple[str, str | None] | None:
    """Parse a single line of a .env file.

    Args:
        line: The line to parse (already stripped of leading/trailing whitespace).
        line_num: Line number for error reporting.

    Returns:
        Tuple of (key, value) if the line is a valid KEY=value format.
        Value is None for empty values.
        Returns None if the line cannot be parsed as KEY=value.
    """
    # Must contain an = sign to be a valid KEY=value line
    if "=" not in line:
        return None

    # Split on first = only
    key, _, value = line.partition("=")
    key = key.strip()

    # Key must not be empty and must be a valid identifier-like name
    if not key:
        return None

    # Key should match typical environment variable naming conventions
    # Allow letters, numbers, underscores (and hyphens for some systems)
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_-]*$", key):
        return None

    # Process value
    value = value.strip()

    # Handle empty value
    if not value:
        return (key, None)

    # Handle quoted values
    if len(value) >= 2:
        # Double quotes
        if value.startswith('"') and value.endswith('"'):
            return (key, value[1:-1])
        # Single quotes
        if value.startswith("'") and value.endswith("'"):
            return (key, value[1:-1])

    # Unquoted value - use as-is
    return (key, value)
