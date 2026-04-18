"""Tests for EnvSentry CLI commands."""

from __future__ import annotations
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from envsentry.cli import app
from envsentry.exit_codes import EXIT_SUCCESS, EXIT_AUDIT_FAILED, EXIT_ERROR


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a sample project with .env and .env.example files."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create a valid .env.example
    env_example = project_dir / ".env.example"
    env_example.write_text(
        "DATABASE_URL=\n"
        "API_KEY=\n"
        "DEBUG=false\n"
    )

    # Create a valid .env with all required vars
    env_file = project_dir / ".env"
    env_file.write_text(
        "DATABASE_URL=postgres://localhost/db\n"
        "API_KEY=test_key_12345\n"
        "DEBUG=true\n"
    )

    return project_dir


@pytest.fixture
def failing_project(tmp_path: Path) -> Path:
    """Create a project that will fail audit (missing required variables)."""
    project_dir = tmp_path / "failing_project"
    project_dir.mkdir()

    # Create .env.example with required vars
    env_example = project_dir / ".env.example"
    env_example.write_text(
        "DATABASE_URL=\n"
        "API_KEY=\n"
    )

    # Create .env missing API_KEY
    env_file = project_dir / ".env"
    env_file.write_text(
        "DATABASE_URL=postgres://localhost/db\n"
    )

    return project_dir


@pytest.fixture
def invalid_project(tmp_path: Path) -> Path:
    """Create a project with no .env file."""
    project_dir = tmp_path / "invalid_project"
    project_dir.mkdir()
    return project_dir


def test_cli_help(cli_runner: CliRunner) -> None:
    """Test that --help displays useful information."""
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "envsentry" in result.stdout.lower()
    assert "scan" in result.stdout
    assert "init" in result.stdout


def test_scan_help(cli_runner: CliRunner) -> None:
    """Test that scan --help displays command information."""
    result = cli_runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0
    assert "scan" in result.stdout.lower()
    assert "--path" in result.stdout
    assert "--env-file" in result.stdout
    assert "--format" in result.stdout


def test_init_help(cli_runner: CliRunner) -> None:
    """Test that init --help displays command information."""
    result = cli_runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout.lower()
    assert "--path" in result.stdout


def test_scan_valid_project(cli_runner: CliRunner, sample_project: Path) -> None:
    """Test scan command with valid project returns exit code 0."""
    result = cli_runner.invoke(app, ["scan", "--path", str(sample_project)])
    assert result.exit_code == EXIT_SUCCESS
    assert "EnvSentry Security Audit" in result.stdout
    # Path may be wrapped/split by Rich, just check project name is in output
    assert "test_project" in result.stdout


def test_scan_failing_audit(cli_runner: CliRunner, failing_project: Path) -> None:
    """Test scan command with audit failures returns exit code 1."""
    result = cli_runner.invoke(app, ["scan", "--path", str(failing_project)])
    assert result.exit_code == EXIT_AUDIT_FAILED
    assert "error" in result.stdout.lower()


def test_scan_invalid_project(cli_runner: CliRunner, invalid_project: Path) -> None:
    """Test scan command with missing .env returns appropriate handling."""
    # This should complete but may have warnings
    result = cli_runner.invoke(app, ["scan", "--path", str(invalid_project)])
    # Should not crash - exit code depends on whether missing .env is error or warning
    assert result.exit_code in (EXIT_SUCCESS, EXIT_AUDIT_FAILED)


def test_scan_json_format(cli_runner: CliRunner, sample_project: Path) -> None:
    """Test scan command with JSON format produces valid JSON."""
    result = cli_runner.invoke(app, ["scan", "--path", str(sample_project), "--format", "json"])
    assert result.exit_code == EXIT_SUCCESS

    # Verify output is valid JSON
    data = json.loads(result.stdout)

    # Check required fields
    assert "tool_version" in data
    assert "project_path" in data
    assert "scan_timestamp" in data
    assert "summary" in data
    assert "findings" in data

    # Verify project path is present (normalize path separators)
    assert "test_project" in data["project_path"]


def test_scan_invalid_format(cli_runner: CliRunner, sample_project: Path) -> None:
    """Test scan command with invalid format returns error."""
    result = cli_runner.invoke(app, ["scan", "--path", str(sample_project), "--format", "xml"])
    assert result.exit_code == EXIT_ERROR
    assert "invalid format" in result.stdout.lower() or "invalid format" in result.stderr.lower()


def test_scan_with_explicit_env_file(cli_runner: CliRunner, tmp_path: Path) -> None:
    """Test scan command with explicit --env-file option."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create custom env file
    custom_env = project_dir / ".env.custom"
    custom_env.write_text("TEST_VAR=value\n")

    result = cli_runner.invoke(
        app,
        ["scan", "--path", str(project_dir), "--env-file", ".env.custom"]
    )

    # Should complete without crashing
    assert result.exit_code in (EXIT_SUCCESS, EXIT_AUDIT_FAILED)


def test_init_creates_config(cli_runner: CliRunner, tmp_path: Path) -> None:
    """Test init command creates .envsentry.toml file."""
    project_dir = tmp_path / "new_project"
    project_dir.mkdir()

    result = cli_runner.invoke(app, ["init", "--path", str(project_dir)])
    assert result.exit_code == EXIT_SUCCESS

    # Check file was created
    config_file = project_dir / ".envsentry.toml"
    assert config_file.exists()

    # Check file has useful content
    content = config_file.read_text()
    assert "EnvSentry Configuration File" in content
    assert "[variables." in content
    assert "required" in content
    assert "type" in content


def test_init_refuses_to_overwrite(cli_runner: CliRunner, tmp_path: Path) -> None:
    """Test init command refuses to overwrite existing .envsentry.toml."""
    project_dir = tmp_path / "existing_project"
    project_dir.mkdir()

    # Create existing config
    config_file = project_dir / ".envsentry.toml"
    config_file.write_text("# Existing config\n")

    result = cli_runner.invoke(app, ["init", "--path", str(project_dir)])
    assert result.exit_code == EXIT_ERROR
    assert "already exists" in result.stdout.lower() or "already exists" in result.stderr.lower()

    # Verify original content preserved
    content = config_file.read_text()
    assert content == "# Existing config\n"


def test_scan_nonexistent_path(cli_runner: CliRunner) -> None:
    """Test scan command with nonexistent path."""
    result = cli_runner.invoke(app, ["scan", "--path", "/nonexistent/path/to/project"])
    # Typer should catch this with path validation
    assert result.exit_code != EXIT_SUCCESS


def test_scan_terminal_format_explicit(cli_runner: CliRunner, sample_project: Path) -> None:
    """Test scan command with explicit terminal format."""
    result = cli_runner.invoke(app, ["scan", "--path", str(sample_project), "--format", "terminal"])
    assert result.exit_code == EXIT_SUCCESS
    assert "EnvSentry Security Audit" in result.stdout


def test_scan_format_case_insensitive(cli_runner: CliRunner, sample_project: Path) -> None:
    """Test scan command format option is case-insensitive."""
    result = cli_runner.invoke(app, ["scan", "--path", str(sample_project), "--format", "JSON"])
    assert result.exit_code == EXIT_SUCCESS

    # Should produce valid JSON
    data = json.loads(result.stdout)
    assert "tool_version" in data


def test_init_default_path(cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test init command uses current directory by default."""
    project_dir = tmp_path / "default_project"
    project_dir.mkdir()

    # Change to project directory
    monkeypatch.chdir(project_dir)

    result = cli_runner.invoke(app, ["init"])
    assert result.exit_code == EXIT_SUCCESS

    config_file = project_dir / ".envsentry.toml"
    assert config_file.exists()


def test_scan_output_never_contains_secrets(cli_runner: CliRunner, sample_project: Path) -> None:
    """Test that scan output NEVER contains actual environment variable values."""
    # Add a file with a realistic secret
    env_file = sample_project / ".env"
    env_file.write_text(
        "DATABASE_URL=postgres://user:SECRETPASS@localhost/db\n"
        "API_KEY=sk-proj-super_secret_key_12345\n"
    )

    # Test terminal format
    result = cli_runner.invoke(app, ["scan", "--path", str(sample_project)])
    output = result.stdout

    # Rich may truncate output, but we check for secrets regardless
    # The important check is that secrets are NOT present
    
    # Should NEVER show actual values
    assert "SECRETPASS" not in output
    assert "sk-proj-super_secret_key_12345" not in output

    # Test JSON format
    result = cli_runner.invoke(app, ["scan", "--path", str(sample_project), "--format", "json"])
    json_output = result.stdout

    # Should NOT contain secrets in JSON either
    assert "SECRETPASS" not in json_output
    assert "sk-proj-super_secret_key_12345" not in json_output

    # Verify JSON structure doesn't have value fields
    data = json.loads(json_output)
    for finding in data.get("findings", []):
        assert "value" not in finding
