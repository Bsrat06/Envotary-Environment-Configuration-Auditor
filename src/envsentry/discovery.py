"""File discovery for EnvSentry.

This module provides functionality to locate .env, .env.example, and
.envsentry.toml configuration files within a project directory.
"""

from __future__ import annotations
from pathlib import Path


def discover_files(
    project_path: Path,
    env_file: str | None = None,
    example_file: str | None = None,
) -> dict[str, Path | None]:
    """Discover environment and configuration files in a project.

    Args:
        project_path: Root directory of the project to scan.
        env_file: Optional explicit path to .env file (relative to project_path or absolute).
        example_file: Optional explicit path to .env.example file (relative to project_path or absolute).

    Returns:
        Dictionary with keys:
            - 'env_file': Path to .env file, or None if not found.
            - 'example_file': Path to .env.example file, or None if not found.
            - 'config_file': Path to .envsentry.toml file, or None if not found.
    """
    result: dict[str, Path | None] = {
        "env_file": None,
        "example_file": None,
        "config_file": None,
    }

    # Resolve project path
    project_path = project_path.resolve()

    # Discover .env file
    if env_file:
        # User provided explicit path
        env_path = Path(env_file)
        if not env_path.is_absolute():
            env_path = project_path / env_path
        if env_path.exists() and env_path.is_file():
            result["env_file"] = env_path
    else:
        # Default: look for .env in project root
        default_env = project_path / ".env"
        if default_env.exists() and default_env.is_file():
            result["env_file"] = default_env

    # Discover .env.example file
    if example_file:
        # User provided explicit path
        example_path = Path(example_file)
        if not example_path.is_absolute():
            example_path = project_path / example_path
        if example_path.exists() and example_path.is_file():
            result["example_file"] = example_path
    else:
        # Default: look for .env.example in project root
        default_example = project_path / ".env.example"
        if default_example.exists() and default_example.is_file():
            result["example_file"] = default_example

    # Discover .envsentry.toml config file
    config_path = project_path / ".envsentry.toml"
    if config_path.exists() and config_path.is_file():
        result["config_file"] = config_path

    return result
