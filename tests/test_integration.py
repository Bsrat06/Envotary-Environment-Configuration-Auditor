"""Integration tests for complete audit workflows."""

from pathlib import Path
import pytest

from envsentry.engine import run_audit


def test_integration_valid_project(tmp_path):
    """Test complete audit flow for a valid project."""
    # Create .env file
    (tmp_path / ".env").write_text("""
DATABASE_URL=postgres://localhost:5432/mydb
REDIS_URL=redis://localhost:6379
API_KEY=sk-1234567890abcdefghij
DEBUG=false
PORT=8080
ENVIRONMENT=production
""")

    # Create .env.example
    (tmp_path / ".env.example").write_text("""
DATABASE_URL=postgres://localhost/dbname
REDIS_URL=redis://localhost
API_KEY=your-api-key
DEBUG=false
PORT=8080
ENVIRONMENT=development
""")

    # Create .envsentry.toml
    (tmp_path / ".envsentry.toml").write_text("""
[variables.DATABASE_URL]
required = true
type = "url"
secret = true

[variables.REDIS_URL]
required = true
type = "url"
secret = true

[variables.API_KEY]
required = true
type = "string"
secret = true
min_length = 20

[variables.DEBUG]
required = false
type = "boolean"

[variables.PORT]
required = false
type = "integer"
min = 1024
max = 65535

[variables.ENVIRONMENT]
required = true
type = "string"
choices = ["development", "staging", "production"]
""")

    result = run_audit(tmp_path)

    # Should have no errors (valid configuration)
    assert result.summary.get("error", 0) == 0
    assert result.project_path == str(tmp_path.resolve())


def test_integration_missing_variables(tmp_path):
    """Test audit flow detecting multiple missing required variables."""
    # Create incomplete .env file
    (tmp_path / ".env").write_text("""
DATABASE_URL=postgres://localhost:5432/mydb
PORT=8080
""")

    # Create .env.example defining all required vars
    (tmp_path / ".env.example").write_text("""
DATABASE_URL=
REDIS_URL=
API_KEY=
PORT=
SECRET_KEY=
""")

    result = run_audit(tmp_path)

    # Should detect missing REDIS_URL, API_KEY, SECRET_KEY
    missing_vars = [f.variable for f in result.findings if f.code == "ENV001"]
    assert set(missing_vars) == {"REDIS_URL", "API_KEY", "SECRET_KEY"}
    assert result.summary["error"] >= 3


def test_integration_type_violations(tmp_path):
    """Test audit flow detecting multiple type violations."""
    # Create .env with type errors
    (tmp_path / ".env").write_text("""
PORT=not-a-number
DEBUG=maybe
TIMEOUT=abc
RATE=not-a-float
DATABASE_URL=not a url
""")

    # Create config with type constraints
    (tmp_path / ".envsentry.toml").write_text("""
[variables.PORT]
type = "integer"

[variables.DEBUG]
type = "boolean"

[variables.TIMEOUT]
type = "integer"

[variables.RATE]
type = "float"

[variables.DATABASE_URL]
type = "url"
""")

    result = run_audit(tmp_path)

    # Should detect all type errors
    type_errors = [f.variable for f in result.findings if f.code == "ENV005"]
    url_errors = [f.variable for f in result.findings if f.code == "ENV006"]

    assert set(type_errors) == {"PORT", "DEBUG", "TIMEOUT", "RATE"}
    assert set(url_errors) == {"DATABASE_URL"}
    assert result.summary["error"] >= 5


def test_integration_constraint_violations(tmp_path):
    """Test audit flow detecting constraint violations."""
    # Create .env with constraint violations
    (tmp_path / ".env").write_text("""
SHORT_KEY=abc
LONG_KEY=abcdefghijklmnopqrstuvwxyz1234567890
LOW_PORT=80
HIGH_PORT=99999
NEGATIVE_VAL=-5
""")

    # Create config with constraints
    (tmp_path / ".envsentry.toml").write_text("""
[variables.SHORT_KEY]
min_length = 10

[variables.LONG_KEY]
max_length = 20

[variables.LOW_PORT]
type = "integer"
min = 1024

[variables.HIGH_PORT]
type = "integer"
max = 65535

[variables.NEGATIVE_VAL]
type = "integer"
min = 0
""")

    result = run_audit(tmp_path)

    # Should detect all constraint violations
    length_errors = [f.variable for f in result.findings if f.code == "ENV009"]
    numeric_errors = [f.variable for f in result.findings if f.code == "ENV010"]

    assert set(length_errors) == {"SHORT_KEY", "LONG_KEY"}
    assert set(numeric_errors) == {"LOW_PORT", "HIGH_PORT", "NEGATIVE_VAL"}


def test_integration_placeholder_detection(tmp_path):
    """Test audit flow detecting placeholder values."""
    # Create .env with placeholders
    (tmp_path / ".env").write_text("""
API_KEY=your-api-key-here
DATABASE_URL=replace-me
SECRET=example-secret
TOKEN=<your-token>
TEST_VAR=xxx
VALID_VAR=actual-real-value-12345
""")

    # Create minimal config
    (tmp_path / ".envsentry.toml").write_text("""
[variables.API_KEY]
[variables.DATABASE_URL]
[variables.SECRET]
[variables.TOKEN]
[variables.TEST_VAR]
[variables.VALID_VAR]
""")

    result = run_audit(tmp_path)

    # Should detect placeholders
    placeholder_vars = [f.variable for f in result.findings if f.code == "ENV008"]
    assert "API_KEY" in placeholder_vars
    assert "DATABASE_URL" in placeholder_vars
    assert "SECRET" in placeholder_vars
    assert "TOKEN" in placeholder_vars
    assert "TEST_VAR" in placeholder_vars
    assert "VALID_VAR" not in placeholder_vars


def test_integration_no_value_leakage(tmp_path):
    """Test that no actual environment variable values are leaked in findings."""
    # Create .env with secret values
    (tmp_path / ".env").write_text("""
SECRET_KEY=super-secret-password-12345
API_TOKEN=token-abcdefghijklmnop
DATABASE_PASSWORD=P@ssw0rd!VerySecret
CREDIT_CARD=4532-1234-5678-9010
""")

    # Create config that will trigger various errors
    (tmp_path / ".envsentry.toml").write_text("""
[variables.SECRET_KEY]
secret = true
type = "integer"

[variables.API_TOKEN]
secret = true
min_length = 100

[variables.DATABASE_PASSWORD]
secret = true
type = "boolean"

[variables.CREDIT_CARD]
secret = true
choices = ["visa", "mastercard"]
""")

    result = run_audit(tmp_path)

    # Should have errors but no leaked values
    assert len(result.findings) > 0

    # Check all findings for leaked secrets
    secret_values = [
        "super-secret-password-12345",
        "token-abcdefghijklmnop",
        "P@ssw0rd!VerySecret",
        "4532-1234-5678-9010",
    ]

    for finding in result.findings:
        for secret in secret_values:
            assert secret not in finding.code
            assert secret not in finding.message
            assert secret not in finding.remediation
            assert secret not in str(finding.line)
            # Variable name should be present, but not the value
            if finding.variable in ["SECRET_KEY", "API_TOKEN", "DATABASE_PASSWORD", "CREDIT_CARD"]:
                assert finding.variable in finding.message


def test_integration_empty_project(tmp_path):
    """Test audit on completely empty project directory."""
    result = run_audit(tmp_path)

    # Should report missing .env file
    assert any(f.code == "ENV_FILE_MISSING" for f in result.findings)
    assert result.summary.get("warning", 0) > 0


def test_integration_example_only(tmp_path):
    """Test audit with only .env.example (no actual .env)."""
    # Create only .env.example
    (tmp_path / ".env.example").write_text("""
DATABASE_URL=
API_KEY=
""")

    result = run_audit(tmp_path)

    # Should report missing .env file
    assert any(f.code == "ENV_FILE_MISSING" for f in result.findings)


def test_integration_config_priority(tmp_path):
    """Test that .envsentry.toml takes priority over .env.example."""
    # Create .env
    (tmp_path / ".env").write_text("VAR1=value1\n")

    # Create .env.example (would infer VAR1 as required)
    (tmp_path / ".env.example").write_text("VAR1=\nVAR2=\n")

    # Create .envsentry.toml (VAR2 is optional)
    (tmp_path / ".envsentry.toml").write_text("""
[variables.VAR1]
required = true

[variables.VAR2]
required = false
""")

    result = run_audit(tmp_path)

    # Should NOT report VAR2 as missing (it's optional per config)
    missing_vars = [f.variable for f in result.findings if f.code == "ENV001"]
    assert "VAR2" not in missing_vars


def test_integration_duplicate_handling(tmp_path):
    """Test audit properly handles duplicate variable definitions."""
    # Create .env with multiple duplicates
    (tmp_path / ".env").write_text("""
VAR1=first
VAR2=value
VAR1=second
VAR3=another
VAR1=third
VAR2=duplicate
""")

    result = run_audit(tmp_path)

    # Should report duplicates
    duplicate_findings = [f for f in result.findings if f.code == "ENV003"]
    assert len(duplicate_findings) == 2  # VAR1 and VAR2

    duplicate_vars = {f.variable for f in duplicate_findings}
    assert duplicate_vars == {"VAR1", "VAR2"}
