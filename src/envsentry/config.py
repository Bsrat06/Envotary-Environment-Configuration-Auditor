"""Configuration and schema loading for EnvSentry.

This module handles parsing .envsentry.toml configuration files and
inferring schemas from .env.example files.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from envsentry.models import ParsedEnvFile


@dataclass
class SchemaVariable:
    """Schema definition for a single environment variable.

    Attributes:
        required: Whether this variable must be defined.
        type: Variable type ('string', 'integer', 'float', 'boolean', 'url').
        secret: Whether this variable contains sensitive data.
        min_length: Minimum string length constraint (for string/url types).
        max_length: Maximum string length constraint (for string/url types).
        min: Minimum numeric value constraint (for integer/float types).
        max: Maximum numeric value constraint (for integer/float types).
        choices: List of allowed values (for string types).
    """

    required: bool = True
    type: str = "string"
    secret: bool = False
    min_length: int | None = None
    max_length: int | None = None
    min: float | None = None
    max: float | None = None
    choices: list[str] | None = None


def load_config(config_path: Path | None) -> dict[str, SchemaVariable]:
    """Load schema configuration from .envsentry.toml file.

    Args:
        config_path: Path to .envsentry.toml file, or None if no config exists.

    Returns:
        Dictionary mapping variable names to SchemaVariable objects.
        Returns empty dict if config_path is None.

    Raises:
        FileNotFoundError: If config_path is provided but file doesn't exist.
        ValueError: If TOML is invalid or contains unknown properties.
    """
    if config_path is None:
        return {}

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid TOML in {config_path}: {e}")
    except OSError as e:
        raise ValueError(f"Failed to read config file {config_path}: {e}")

    # Parse [variables] section
    variables_section = data.get("variables", {})
    if not isinstance(variables_section, dict):
        raise ValueError(f"[variables] section must be a table in {config_path}")

    schema: dict[str, SchemaVariable] = {}
    valid_properties = {
        "required",
        "type",
        "secret",
        "min_length",
        "max_length",
        "min",
        "max",
        "choices",
    }

    for var_name, var_config in variables_section.items():
        if not isinstance(var_config, dict):
            raise ValueError(
                f"Variable '{var_name}' must be a table in {config_path}"
            )

        # Check for unknown properties
        unknown = set(var_config.keys()) - valid_properties
        if unknown:
            raise ValueError(
                f"Unknown properties for variable '{var_name}' in {config_path}: {', '.join(sorted(unknown))}"
            )

        # Extract properties with defaults
        schema[var_name] = SchemaVariable(
            required=var_config.get("required", True),
            type=var_config.get("type", "string"),
            secret=var_config.get("secret", False),
            min_length=var_config.get("min_length"),
            max_length=var_config.get("max_length"),
            min=var_config.get("min"),
            max=var_config.get("max"),
            choices=var_config.get("choices"),
        )

    return schema


def infer_schema_from_example(
    example_file: ParsedEnvFile,
) -> dict[str, SchemaVariable]:
    """Infer a basic schema from a .env.example file.

    Creates a schema where all variables found in the example are marked as
    required string type with no additional constraints.

    Args:
        example_file: Parsed .env.example file.

    Returns:
        Dictionary mapping variable names to basic SchemaVariable objects.
    """
    schema: dict[str, SchemaVariable] = {}

    for var in example_file.variables:
        schema[var.name] = SchemaVariable(
            required=True,
            type="string",
            secret=False,
        )

    return schema
