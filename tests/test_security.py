"""Security-focused tests for EnvSentry.

This test suite verifies that actual environment variable values are NEVER exposed
in any output channel: terminal reports, JSON reports, ValidationFinding objects,
exception messages, or error tracebacks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envsentry import validators
from envsentry.config import SchemaVariable
from envsentry.models import AuditResult, EnvVariable, ParsedEnvFile, ValidationFinding
from envsentry.reporters.json import JSONReporter
from envsentry.reporters.terminal import TerminalReporter

# Test secrets that should NEVER appear in output
TEST_SECRET_1 = "SUPER_SECRET_KEY_12345"
TEST_SECRET_2 = "p@ssw0rd_S3cur3_9876"
TEST_SECRET_3 = "api-token-XyZ-AbC-123"


def test_terminal_reporter_never_leaks_secrets(capsys: pytest.CaptureFixture) -> None:
    """Test that terminal reporter NEVER displays actual environment variable values."""
    # Create findings with secret values in the env vars
    env_vars = {
        "API_KEY": EnvVariable("API_KEY", TEST_SECRET_1, 1, ".env"),
        "PASSWORD": EnvVariable("PASSWORD", TEST_SECRET_2, 2, ".env"),
        "TOKEN": EnvVariable("TOKEN", TEST_SECRET_3, 3, ".env"),
    }
    schema = {
        "API_KEY": SchemaVariable(required=True, min_length=100),  # Will fail
        "PASSWORD": SchemaVariable(type="integer"),  # Will fail type check
        "TOKEN": SchemaVariable(choices=["prod", "dev"]),  # Will fail choices
    }

    # Run validators to generate findings
    findings: list[ValidationFinding] = []
    findings.extend(validators.check_invalid_types(env_vars, schema))
    findings.extend(validators.check_length_constraints(env_vars, schema))
    findings.extend(validators.check_invalid_choices(env_vars, schema))

    # Create audit result
    audit_result = AuditResult(
        project_path="/test/project",
        findings=findings,
        summary={"error": len(findings)},
    )

    # Generate terminal report
    reporter = TerminalReporter()
    reporter.report(audit_result)

    # Capture output
    captured = capsys.readouterr()
    output = captured.out + captured.err

    # CRITICAL: Verify NO secrets appear in terminal output
    assert TEST_SECRET_1 not in output, "Terminal reporter leaked TEST_SECRET_1"
    assert TEST_SECRET_2 not in output, "Terminal reporter leaked TEST_SECRET_2"
    assert TEST_SECRET_3 not in output, "Terminal reporter leaked TEST_SECRET_3"

    # Verify variable names DO appear (proving output exists)
    assert "API_KEY" in output
    assert "PASSWORD" in output
    assert "TOKEN" in output


def test_json_reporter_never_leaks_secrets() -> None:
    """Test that JSON reporter NEVER includes actual environment variable values."""
    # Create findings with secret values in the env vars
    env_vars = {
        "API_KEY": EnvVariable("API_KEY", TEST_SECRET_1, 1, ".env"),
        "DATABASE_PASSWORD": EnvVariable("DATABASE_PASSWORD", TEST_SECRET_2, 2, ".env"),
    }
    schema = {
        "API_KEY": SchemaVariable(required=True, min_length=50),  # Will fail
        "DATABASE_PASSWORD": SchemaVariable(type="boolean"),  # Will fail type check
    }

    # Run validators
    findings: list[ValidationFinding] = []
    findings.extend(validators.check_invalid_types(env_vars, schema))
    findings.extend(validators.check_length_constraints(env_vars, schema))

    # Create audit result
    audit_result = AuditResult(
        project_path="/test/project",
        findings=findings,
        summary={"error": len(findings)},
    )

    # Generate JSON report (returns string directly)
    reporter = JSONReporter()
    json_output = reporter.report(audit_result)

    # CRITICAL: Verify NO secrets appear in JSON output
    assert TEST_SECRET_1 not in json_output, "JSON reporter leaked TEST_SECRET_1"
    assert TEST_SECRET_2 not in json_output, "JSON reporter leaked TEST_SECRET_2"

    # Verify the JSON is valid and contains expected structure
    parsed = json.loads(json_output)
    assert "findings" in parsed
    assert len(parsed["findings"]) > 0
    assert "summary" in parsed

    # Deep check: ensure secrets not in any JSON field
    json_str_deep = json.dumps(parsed)
    assert TEST_SECRET_1 not in json_str_deep, "Secret found in parsed JSON structure"
    assert TEST_SECRET_2 not in json_str_deep, "Secret found in parsed JSON structure"


def test_validation_finding_never_stores_secrets() -> None:
    """Test that ValidationFinding objects never contain actual env variable values."""
    # Create env vars with secret values
    env_vars = {
        "SECRET_KEY": EnvVariable("SECRET_KEY", TEST_SECRET_1, 1, ".env"),
        "API_TOKEN": EnvVariable("API_TOKEN", TEST_SECRET_2, 2, ".env"),
    }
    schema = {
        "SECRET_KEY": SchemaVariable(required=True, min_length=100),
        "API_TOKEN": SchemaVariable(type="integer"),
    }

    # Run all validators
    all_findings: list[ValidationFinding] = []
    all_findings.extend(validators.check_missing_required(env_vars, schema))
    all_findings.extend(validators.check_undocumented(env_vars, schema))
    all_findings.extend(validators.check_empty_required(env_vars, schema))
    all_findings.extend(validators.check_invalid_types(env_vars, schema))
    all_findings.extend(validators.check_invalid_urls(env_vars, schema))
    all_findings.extend(validators.check_invalid_choices(env_vars, schema))
    all_findings.extend(validators.check_placeholders(env_vars, schema))
    all_findings.extend(validators.check_length_constraints(env_vars, schema))
    all_findings.extend(validators.check_numeric_constraints(env_vars, schema))

    # Check every finding object
    for finding in all_findings:
        # Check all string fields in ValidationFinding
        assert TEST_SECRET_1 not in finding.code, f"Secret in finding.code: {finding.code}"
        assert TEST_SECRET_1 not in finding.message, f"Secret in finding.message: {finding.message}"
        assert TEST_SECRET_1 not in finding.remediation, f"Secret in finding.remediation: {finding.remediation}"
        assert TEST_SECRET_1 not in finding.file, f"Secret in finding.file: {finding.file}"

        assert TEST_SECRET_2 not in finding.code, f"Secret in finding.code: {finding.code}"
        assert TEST_SECRET_2 not in finding.message, f"Secret in finding.message: {finding.message}"
        assert TEST_SECRET_2 not in finding.remediation, f"Secret in finding.remediation: {finding.remediation}"
        assert TEST_SECRET_2 not in finding.file, f"Secret in finding.file: {finding.file}"


def test_exception_messages_never_leak_secrets(tmp_path: Path) -> None:
    """Test that exceptions triggered by parsing/validation never expose secret values."""
    # Create a .env file with secrets
    env_file = tmp_path / ".env"
    env_file.write_text(f"SECRET_KEY={TEST_SECRET_1}\nPASSWORD={TEST_SECRET_2}\n")

    # Import parser to test exception handling
    from envsentry.parser import parse_dotenv_file

    # Parse the file (should succeed)
    parsed = parse_dotenv_file(env_file)

    # Verify parsed file doesn't expose secrets directly
    assert TEST_SECRET_1 not in str(parsed.path)
    # Note: parsed.variables will contain the secrets, but we're testing
    # that error messages and exceptions don't leak them

    # Test with malformed file that might trigger parse errors
    malformed_file = tmp_path / ".env.malformed"
    malformed_file.write_text(f'SECRET={TEST_SECRET_1}\nBAD_LINE="unclosed string\n')

    # Even if parsing fails, the exception message should not contain secrets
    try:
        parsed_bad = parse_dotenv_file(malformed_file)
        # If it succeeds despite malformation, that's okay for this test
        # We're primarily checking that no exceptions leak secrets
    except Exception as e:
        error_message = str(e)
        assert TEST_SECRET_1 not in error_message, f"Exception message leaked secret: {error_message}"


def test_audit_result_summary_never_leaks_secrets() -> None:
    """Test that AuditResult summary doesn't contain any secret values."""
    # Create findings with secrets
    findings = [
        ValidationFinding(
            code="ENV005",
            severity="error",
            variable="API_KEY",
            file=".env",
            line=1,
            message="Variable 'API_KEY' must be an integer",
            remediation="Ensure API_KEY contains a valid integer value",
        ),
        ValidationFinding(
            code="ENV009",
            severity="error",
            variable="PASSWORD",
            file=".env",
            line=2,
            message="Variable 'PASSWORD' is too short",
            remediation="Ensure PASSWORD has at least 20 characters",
        ),
    ]

    audit_result = AuditResult(
        project_path="/test/project",
        findings=findings,
        summary={"error": 2, "warning": 0},
    )

    # Convert to string representation and check
    result_str = str(audit_result)
    assert TEST_SECRET_1 not in result_str
    assert TEST_SECRET_2 not in result_str

    # Check summary specifically
    summary_str = str(audit_result.summary)
    assert TEST_SECRET_1 not in summary_str
    assert TEST_SECRET_2 not in summary_str


def test_placeholder_detection_with_secrets() -> None:
    """Test that placeholder detection identifies placeholders but doesn't leak actual secrets."""
    env_vars = {
        "PLACEHOLDER": EnvVariable("PLACEHOLDER", "your-api-key-here", 1, ".env"),
        "ACTUAL_SECRET": EnvVariable("ACTUAL_SECRET", TEST_SECRET_1, 2, ".env"),
    }
    schema = {
        "PLACEHOLDER": SchemaVariable(),
        "ACTUAL_SECRET": SchemaVariable(),
    }

    findings = validators.check_placeholders(env_vars, schema)

    # Should detect the placeholder
    placeholder_vars = {f.variable for f in findings}
    assert "PLACEHOLDER" in placeholder_vars

    # Check that none of the findings contain the actual secret
    for finding in findings:
        assert TEST_SECRET_1 not in finding.message
        assert TEST_SECRET_1 not in finding.remediation


def test_duplicate_detection_never_leaks_values() -> None:
    """Test that duplicate detection doesn't expose the duplicate values."""
    parsed = ParsedEnvFile(
        path=".env",
        variables=[
            EnvVariable("SECRET_KEY", TEST_SECRET_1, 1, ".env"),
            EnvVariable("SECRET_KEY", TEST_SECRET_2, 5, ".env"),  # Different value
            EnvVariable("API_TOKEN", TEST_SECRET_3, 3, ".env"),
        ],
        duplicates={"SECRET_KEY": [1, 5]},
    )

    findings = validators.check_duplicates(parsed)

    # Should find the duplicate
    assert len(findings) == 1
    assert findings[0].variable == "SECRET_KEY"

    # CRITICAL: Should NOT expose either value
    assert TEST_SECRET_1 not in findings[0].message
    assert TEST_SECRET_2 not in findings[0].message
    assert TEST_SECRET_1 not in findings[0].remediation
    assert TEST_SECRET_2 not in findings[0].remediation


def test_empty_required_detection_no_value_leak() -> None:
    """Test that empty required variable detection doesn't leak other variable values."""
    env_vars = {
        "EMPTY_VAR": EnvVariable("EMPTY_VAR", "", 1, ".env"),
        "SECRET_VAR": EnvVariable("SECRET_VAR", TEST_SECRET_1, 2, ".env"),
    }
    schema = {
        "EMPTY_VAR": SchemaVariable(required=True),
        "SECRET_VAR": SchemaVariable(required=True),
    }

    findings = validators.check_empty_required(env_vars, schema)

    # Should only find EMPTY_VAR as empty
    assert len(findings) == 1
    assert findings[0].variable == "EMPTY_VAR"

    # Should NOT mention the secret from another variable
    assert TEST_SECRET_1 not in findings[0].message
    assert TEST_SECRET_1 not in findings[0].remediation


def test_all_validators_with_multiple_secrets() -> None:
    """Comprehensive test: run all validators with multiple secret values and verify no leaks."""
    secrets = {
        "SECRET_1": TEST_SECRET_1,
        "SECRET_2": TEST_SECRET_2,
        "SECRET_3": TEST_SECRET_3,
    }

    env_vars = {
        name: EnvVariable(name, value, idx + 1, ".env")
        for idx, (name, value) in enumerate(secrets.items())
    }

    schema = {
        "SECRET_1": SchemaVariable(required=True, type="integer", min_length=100),
        "SECRET_2": SchemaVariable(required=True, type="boolean", max_length=5),
        "SECRET_3": SchemaVariable(required=True, choices=["option1", "option2"]),
    }

    # Run ALL validators
    all_findings: list[ValidationFinding] = []
    all_findings.extend(validators.check_missing_required(env_vars, schema))
    all_findings.extend(validators.check_undocumented(env_vars, schema))
    all_findings.extend(validators.check_empty_required(env_vars, schema))
    all_findings.extend(validators.check_invalid_types(env_vars, schema))
    all_findings.extend(validators.check_invalid_urls(env_vars, schema))
    all_findings.extend(validators.check_invalid_choices(env_vars, schema))
    all_findings.extend(validators.check_placeholders(env_vars, schema))
    all_findings.extend(validators.check_length_constraints(env_vars, schema))
    all_findings.extend(validators.check_numeric_constraints(env_vars, schema))

    # Convert all findings to strings and verify no secrets
    for finding in all_findings:
        finding_str = (
            f"{finding.code} {finding.severity} {finding.variable} "
            f"{finding.file} {finding.message} {finding.remediation}"
        )
        for secret_value in secrets.values():
            assert secret_value not in finding_str, f"Secret leaked in finding: {finding_str}"
