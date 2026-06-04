"""Tests for EnvSentry reporters (terminal and JSON)."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from envsentry.models import AuditResult, ValidationFinding
from envsentry.reporters.json import JSONReporter
from envsentry.reporters.terminal import TerminalReporter


def test_terminal_reporter_no_findings(capsys: pytest.CaptureFixture) -> None:
    """Test terminal reporter with clean audit (no findings)."""
    audit_result = AuditResult(
        project_path="/test/project",
        findings=[],
        summary={"error": 0, "warning": 0, "info": 0},
    )

    reporter = TerminalReporter()
    reporter.report(audit_result)

    captured = capsys.readouterr()
    assert "EnvSentry Security Audit" in captured.out
    assert "/test/project" in captured.out
    assert "No issues found" in captured.out
    assert "Audit passed" in captured.out


def test_terminal_reporter_with_findings(capsys: pytest.CaptureFixture) -> None:
    """Test terminal reporter displays findings correctly."""
    findings = [
        ValidationFinding(
            code="ENV001",
            severity="error",
            variable="DATABASE_PASSWORD",
            file="/test/.env",
            line=10,
            message="Required variable is missing",
            remediation="Add DATABASE_PASSWORD to your .env file",
        ),
        ValidationFinding(
            code="ENV002",
            severity="warning",
            variable="API_KEY",
            file="/test/.env",
            line=15,
            message="Variable is undocumented",
            remediation="Add API_KEY to .env.example or .envsentry.toml",
        ),
    ]

    audit_result = AuditResult(
        project_path="/test/project",
        findings=findings,
        summary={"error": 1, "warning": 1, "info": 0},
    )

    reporter = TerminalReporter()
    reporter.report(audit_result)

    captured = capsys.readouterr()
    output = captured.out

    # Check header
    assert "EnvSentry Security Audit" in output
    assert "/test/project" in output

    # Check summary
    assert "1 error(s)" in output
    assert "1 warning(s)" in output

    # Check findings are displayed (may be truncated by Rich)
    assert "DATABASE_PASSWORD" in output or "DATABA" in output
    assert "Required variable is missing" in output

    assert "API_KEY" in output
    assert "Variable is undocumented" in output

    # Check file:line references
    assert "/test/.env:10" in output
    assert "/test/.env:15" in output

    # Check footer
    assert "Audit failed" in output


def test_terminal_reporter_never_shows_actual_values(capsys: pytest.CaptureFixture) -> None:
    """Test that terminal reporter NEVER displays actual env variable values."""
    # This test ensures we don't accidentally leak secrets in output
    findings = [
        ValidationFinding(
            code="ENV005",
            severity="error",
            variable="SECRET_KEY",
            file="/test/.env",
            line=5,
            message="Variable has invalid format",
            remediation="Check the value format",
        ),
    ]

    audit_result = AuditResult(
        project_path="/test/project",
        findings=findings,
        summary={"error": 1, "warning": 0, "info": 0},
    )

    reporter = TerminalReporter()
    reporter.report(audit_result)

    captured = capsys.readouterr()
    output = captured.out

    # We should see the variable name (may be truncated but at least part of it)
    assert "SECRET" in output

    # But we should NEVER see actual values like this
    # (This is a meta-test - in real scenarios, values wouldn't be in findings anyway)
    assert "super_secret_password_123" not in output
    assert "sk-proj-" not in output


def test_json_reporter_structure() -> None:
    """Test JSON reporter produces valid JSON with correct structure."""
    findings = [
        ValidationFinding(
            code="ENV001",
            severity="error",
            variable="DATABASE_URL",
            file="/test/.env",
            line=10,
            message="Required variable is missing",
            remediation="Add DATABASE_URL to your .env file",
        ),
        ValidationFinding(
            code="ENV003",
            severity="warning",
            variable="DEBUG",
            file="/test/.env",
            line=20,
            message="Variable has placeholder value",
            remediation="Replace placeholder with actual value",
        ),
    ]

    audit_result = AuditResult(
        project_path="/test/project",
        findings=findings,
        summary={"error": 1, "warning": 1, "info": 0},
    )

    reporter = JSONReporter()
    output = reporter.report(audit_result)

    # Parse JSON to verify it's valid
    data = json.loads(output)

    # Check top-level structure
    assert "tool_version" in data
    assert "project_path" in data
    assert "scan_timestamp" in data
    assert "summary" in data
    assert "findings" in data

    # Check values
    assert data["project_path"] == "/test/project"
    assert data["summary"]["total_findings"] == 2
    assert data["summary"]["by_severity"]["error"] == 1
    assert data["summary"]["by_severity"]["warning"] == 1

    # Check timestamp is valid ISO format
    datetime.fromisoformat(data["scan_timestamp"])

    # Check findings
    assert len(data["findings"]) == 2

    finding1 = data["findings"][0]
    assert finding1["code"] == "ENV001"
    assert finding1["severity"] == "error"
    assert finding1["variable"] == "DATABASE_URL"
    assert finding1["file"] == "/test/.env"
    assert finding1["line"] == 10
    assert finding1["message"] == "Required variable is missing"
    assert finding1["remediation"] == "Add DATABASE_URL to your .env file"

    finding2 = data["findings"][1]
    assert finding2["code"] == "ENV003"
    assert finding2["severity"] == "warning"


def test_json_reporter_stable_output() -> None:
    """Test JSON reporter produces deterministic output with sorted keys."""
    findings = [
        ValidationFinding(
            code="ENV001",
            severity="error",
            variable="TEST_VAR",
            file="/test/.env",
            line=1,
            message="Test message",
            remediation="Test remediation",
        ),
    ]

    audit_result = AuditResult(
        project_path="/test/project",
        findings=findings,
        summary={"error": 1, "warning": 0},
    )

    reporter = JSONReporter()
    output1 = reporter.report(audit_result)
    output2 = reporter.report(audit_result)

    # Parse both outputs
    data1 = json.loads(output1)
    data2 = json.loads(output2)

    # Timestamps will differ, so compare structure only
    assert data1["project_path"] == data2["project_path"]
    assert data1["tool_version"] == data2["tool_version"]
    assert data1["summary"] == data2["summary"]
    assert len(data1["findings"]) == len(data2["findings"])

    # Verify keys are sorted (check first few keys)
    output_lines = output1.split("\n")
    # In sorted JSON, "by_severity" comes before "total_findings"
    by_severity_line = next(i for i, line in enumerate(output_lines) if "by_severity" in line)
    total_findings_line = next(i for i, line in enumerate(output_lines) if "total_findings" in line)
    assert by_severity_line < total_findings_line


def test_json_reporter_never_includes_actual_values() -> None:
    """Test that JSON reporter NEVER includes actual env variable values."""
    findings = [
        ValidationFinding(
            code="ENV005",
            severity="error",
            variable="API_SECRET",
            file="/test/.env",
            line=5,
            message="Variable has invalid format",
            remediation="Check the value format",
        ),
    ]

    audit_result = AuditResult(
        project_path="/test/project",
        findings=findings,
        summary={"error": 1, "warning": 0, "info": 0},
    )

    reporter = JSONReporter()
    output = reporter.report(audit_result)
    data = json.loads(output)

    # Verify the structure exists
    assert len(data["findings"]) == 1
    finding = data["findings"][0]

    # Should have variable name
    assert finding["variable"] == "API_SECRET"

    # Should NOT have a "value" field at all
    assert "value" not in finding

    # Should NOT contain common secret patterns in the JSON string
    assert "sk-" not in output
    assert "secret_key_" not in output
    assert "password123" not in output


def test_json_reporter_empty_findings() -> None:
    """Test JSON reporter with no findings."""
    audit_result = AuditResult(
        project_path="/test/project",
        findings=[],
        summary={"error": 0, "warning": 0, "info": 0},
    )

    reporter = JSONReporter()
    output = reporter.report(audit_result)
    data = json.loads(output)

    assert data["summary"]["total_findings"] == 0
    assert data["findings"] == []
    assert data["summary"]["by_severity"]["error"] == 0
    assert data["summary"]["by_severity"]["warning"] == 0


def test_terminal_reporter_groups_by_severity(capsys: pytest.CaptureFixture) -> None:
    """Test terminal reporter groups findings by severity with errors first."""
    findings = [
        ValidationFinding(
            code="ENV003",
            severity="warning",
            variable="WARNING_VAR",
            file="/test/.env",
            line=2,
            message="Warning message",
            remediation="Warning fix",
        ),
        ValidationFinding(
            code="ENV001",
            severity="error",
            variable="ERROR_VAR",
            file="/test/.env",
            line=1,
            message="Error message",
            remediation="Error fix",
        ),
        ValidationFinding(
            code="ENV004",
            severity="info",
            variable="INFO_VAR",
            file="/test/.env",
            line=3,
            message="Info message",
            remediation="Info note",
        ),
    ]

    audit_result = AuditResult(
        project_path="/test/project",
        findings=findings,
        summary={"error": 1, "warning": 1, "info": 1},
    )

    reporter = TerminalReporter()
    reporter.report(audit_result)

    captured = capsys.readouterr()
    output = captured.out

    # Find positions of each severity section
    errors_pos = output.find("Errors:")
    warnings_pos = output.find("Warnings:")
    info_pos = output.find("Information:")

    # Errors should come first, then warnings, then info
    assert errors_pos != -1
    assert warnings_pos != -1
    assert info_pos != -1
    assert errors_pos < warnings_pos < info_pos
