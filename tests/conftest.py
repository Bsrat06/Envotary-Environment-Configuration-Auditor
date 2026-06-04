"""Pytest configuration and shared fixtures for EnvSentry tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from envsentry.config import SchemaVariable
from envsentry.models import AuditResult, EnvVariable, ParsedEnvFile, ValidationFinding


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_project_dir(fixtures_dir: Path) -> Path:
    """Return path to valid project fixture."""
    return fixtures_dir / "valid_project"


@pytest.fixture
def invalid_project_dir(fixtures_dir: Path) -> Path:
    """Return path to invalid project fixture."""
    return fixtures_dir / "invalid_project"


@pytest.fixture
def django_project_dir(fixtures_dir: Path) -> Path:
    """Return path to Django project fixture."""
    return fixtures_dir / "django_project"


@pytest.fixture
def node_project_dir(fixtures_dir: Path) -> Path:
    """Return path to Node.js project fixture."""
    return fixtures_dir / "node_project"


@pytest.fixture
def sample_env_vars() -> dict[str, EnvVariable]:
    """Return sample environment variables for testing."""
    return {
        "DATABASE_URL": EnvVariable(
            "DATABASE_URL", "postgres://localhost:5432/db", 1, ".env"
        ),
        "API_KEY": EnvVariable("API_KEY", "test-api-key-123", 2, ".env"),
        "DEBUG": EnvVariable("DEBUG", "true", 3, ".env"),
        "PORT": EnvVariable("PORT", "8080", 4, ".env"),
    }


@pytest.fixture
def sample_schema() -> dict[str, SchemaVariable]:
    """Return sample schema configuration for testing."""
    return {
        "DATABASE_URL": SchemaVariable(type="url", required=True, secret=True),
        "API_KEY": SchemaVariable(
            type="string", required=True, secret=True, min_length=10
        ),
        "DEBUG": SchemaVariable(type="boolean", required=False),
        "PORT": SchemaVariable(type="integer", required=False, min=1024, max=65535),
    }


@pytest.fixture
def sample_parsed_file() -> ParsedEnvFile:
    """Return sample parsed .env file for testing."""
    return ParsedEnvFile(
        path=".env",
        variables=[
            EnvVariable("VAR1", "value1", 1, ".env"),
            EnvVariable("VAR2", "value2", 2, ".env"),
            EnvVariable("VAR3", "value3", 3, ".env"),
        ],
        duplicates={},
    )


@pytest.fixture
def sample_findings() -> list[ValidationFinding]:
    """Return sample validation findings for testing."""
    return [
        ValidationFinding(
            code="ENV001",
            severity="error",
            variable="MISSING_VAR",
            file="(missing)",
            line=None,
            message="Required variable 'MISSING_VAR' is not defined",
            remediation="Add MISSING_VAR=<value> to your .env file",
        ),
        ValidationFinding(
            code="ENV005",
            severity="error",
            variable="BAD_PORT",
            file=".env",
            line=10,
            message="Variable 'BAD_PORT' must be an integer",
            remediation="Ensure BAD_PORT contains a valid integer value",
        ),
        ValidationFinding(
            code="ENV008",
            severity="warning",
            variable="PLACEHOLDER_KEY",
            file=".env",
            line=5,
            message="Variable 'PLACEHOLDER_KEY' appears to contain a placeholder value",
            remediation="Replace the placeholder in PLACEHOLDER_KEY with an actual value",
        ),
    ]


@pytest.fixture
def sample_audit_result(sample_findings: list[ValidationFinding]) -> AuditResult:
    """Return sample audit result for testing."""
    return AuditResult(
        project_path="/test/project",
        findings=sample_findings,
        summary={"error": 2, "warning": 1},
    )


@pytest.fixture
def temp_env_file(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        """# Test .env file
DATABASE_URL=postgres://localhost:5432/testdb
API_KEY=test-key-123
DEBUG=true
PORT=8080
"""
    )
    yield env_file
    # Cleanup handled by tmp_path


@pytest.fixture
def secret_test_value() -> str:
    """Return a test secret value that should never leak."""
    return "TEST_SECRET_DO_NOT_LEAK_12345"
