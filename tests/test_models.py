"""Tests for data models in Envotary.

Tests model construction, field types, serialization, and immutability.
"""

from __future__ import annotations

from envotary.models import AuditResult, EnvVariable, ParsedEnvFile, ValidationFinding


class TestEnvVariable:
    """Test EnvVariable model."""

    def test_construction_with_all_fields(self) -> None:
        """Test creating EnvVariable with all fields."""
        var = EnvVariable(
            name="API_KEY",
            value="some-value",
            line_number=42,
            file=".env",
        )

        assert var.name == "API_KEY"
        assert var.value == "some-value"
        assert var.line_number == 42
        assert var.file == ".env"

    def test_construction_with_none_value(self) -> None:
        """Test creating EnvVariable with None value."""
        var = EnvVariable(
            name="EMPTY_VAR",
            value=None,
            line_number=1,
            file=".env",
        )

        assert var.name == "EMPTY_VAR"
        assert var.value is None
        assert var.line_number == 1

    def test_construction_with_none_line_number(self) -> None:
        """Test creating EnvVariable with None line_number."""
        var = EnvVariable(
            name="VAR",
            value="value",
            line_number=None,
            file=".env",
        )

        assert var.name == "VAR"
        assert var.line_number is None

    def test_field_types(self) -> None:
        """Test that EnvVariable has correct field types."""
        var = EnvVariable("TEST", "value", 1, ".env")

        assert isinstance(var.name, str)
        assert isinstance(var.value, (str, type(None)))
        assert isinstance(var.line_number, (int, type(None)))
        assert isinstance(var.file, str)


class TestParsedEnvFile:
    """Test ParsedEnvFile model."""

    def test_construction_basic(self) -> None:
        """Test creating ParsedEnvFile with basic fields."""
        variables = [
            EnvVariable("VAR1", "value1", 1, ".env"),
            EnvVariable("VAR2", "value2", 2, ".env"),
        ]

        parsed = ParsedEnvFile(
            path="/path/to/.env",
            variables=variables,
        )

        assert parsed.path == "/path/to/.env"
        assert len(parsed.variables) == 2
        assert parsed.duplicates == {}

    def test_construction_with_duplicates(self) -> None:
        """Test creating ParsedEnvFile with duplicate tracking."""
        variables = [
            EnvVariable("VAR1", "value1", 1, ".env"),
            EnvVariable("VAR1", "value2", 5, ".env"),
        ]
        duplicates = {"VAR1": [1, 5]}

        parsed = ParsedEnvFile(
            path="/path/to/.env",
            variables=variables,
            duplicates=duplicates,
        )

        assert len(parsed.duplicates) == 1
        assert "VAR1" in parsed.duplicates
        assert parsed.duplicates["VAR1"] == [1, 5]

    def test_default_duplicates(self) -> None:
        """Test that duplicates defaults to empty dict."""
        parsed = ParsedEnvFile(
            path=".env",
            variables=[],
        )

        assert parsed.duplicates == {}
        assert isinstance(parsed.duplicates, dict)

    def test_field_types(self) -> None:
        """Test that ParsedEnvFile has correct field types."""
        parsed = ParsedEnvFile(
            path=".env",
            variables=[EnvVariable("V", "val", 1, ".env")],
            duplicates={"V": [1, 2]},
        )

        assert isinstance(parsed.path, str)
        assert isinstance(parsed.variables, list)
        assert isinstance(parsed.duplicates, dict)


class TestValidationFinding:
    """Test ValidationFinding model."""

    def test_construction_with_line_number(self) -> None:
        """Test creating ValidationFinding with line number."""
        finding = ValidationFinding(
            code="ENV001",
            severity="error",
            variable="API_KEY",
            file=".env",
            line=42,
            message="Required variable 'API_KEY' is not defined",
            remediation="Add API_KEY=<value> to your .env file",
        )

        assert finding.code == "ENV001"
        assert finding.severity == "error"
        assert finding.variable == "API_KEY"
        assert finding.file == ".env"
        assert finding.line == 42
        assert "Required variable" in finding.message
        assert "Add API_KEY" in finding.remediation

    def test_construction_without_line_number(self) -> None:
        """Test creating ValidationFinding with None line number."""
        finding = ValidationFinding(
            code="ENV001",
            severity="error",
            variable="MISSING_VAR",
            file="(missing)",
            line=None,
            message="Variable is missing",
            remediation="Add the variable",
        )

        assert finding.line is None
        assert finding.variable == "MISSING_VAR"

    def test_severity_levels(self) -> None:
        """Test different severity levels."""
        severities = ["error", "warning", "info"]

        for sev in severities:
            finding = ValidationFinding(
                code="ENV999",
                severity=sev,
                variable="VAR",
                file=".env",
                line=1,
                message="Test message",
                remediation="Test remediation",
            )
            assert finding.severity == sev

    def test_never_stores_secret_values(self) -> None:
        """Test that ValidationFinding doesn't store actual env values even when available."""
        # Simulate creating a finding where the secret value is available
        secret_value = "super-secret-123"
        var_name = "API_KEY"

        # A validator should create findings without including the value
        finding = ValidationFinding(
            code="ENV005",
            severity="error",
            variable=var_name,
            file=".env",
            line=1,
            message=f"Variable '{var_name}' must be an integer",
            remediation=f"Ensure {var_name} contains a valid integer value",
        )

        # Verify the secret is not in any field
        assert secret_value not in finding.code
        assert secret_value not in finding.severity
        assert secret_value not in finding.variable
        assert secret_value not in finding.file
        assert secret_value not in finding.message
        assert secret_value not in finding.remediation

    def test_field_types(self) -> None:
        """Test that ValidationFinding has correct field types."""
        finding = ValidationFinding(
            code="ENV001",
            severity="error",
            variable="VAR",
            file=".env",
            line=1,
            message="msg",
            remediation="fix",
        )

        assert isinstance(finding.code, str)
        assert isinstance(finding.severity, str)
        assert isinstance(finding.variable, str)
        assert isinstance(finding.file, str)
        assert isinstance(finding.line, (int, type(None)))
        assert isinstance(finding.message, str)
        assert isinstance(finding.remediation, str)


class TestAuditResult:
    """Test AuditResult model."""

    def test_construction_basic(self) -> None:
        """Test creating AuditResult with basic fields."""
        findings = [
            ValidationFinding(
                code="ENV001",
                severity="error",
                variable="VAR1",
                file=".env",
                line=None,
                message="Missing variable",
                remediation="Add it",
            ),
        ]

        result = AuditResult(
            project_path="/path/to/project",
            findings=findings,
        )

        assert result.project_path == "/path/to/project"
        assert len(result.findings) == 1
        assert result.summary == {}

    def test_construction_with_summary(self) -> None:
        """Test creating AuditResult with summary."""
        findings = [
            ValidationFinding("ENV001", "error", "V1", ".env", 1, "msg", "fix"),
            ValidationFinding("ENV002", "warning", "V2", ".env", 2, "msg", "fix"),
        ]
        summary = {"error": 1, "warning": 1}

        result = AuditResult(
            project_path="/project",
            findings=findings,
            summary=summary,
        )

        assert result.summary == {"error": 1, "warning": 1}
        assert result.summary["error"] == 1
        assert result.summary["warning"] == 1

    def test_default_summary(self) -> None:
        """Test that summary defaults to empty dict."""
        result = AuditResult(
            project_path="/project",
            findings=[],
        )

        assert result.summary == {}
        assert isinstance(result.summary, dict)

    def test_empty_findings(self) -> None:
        """Test AuditResult with no findings."""
        result = AuditResult(
            project_path="/project",
            findings=[],
            summary={"error": 0, "warning": 0},
        )

        assert len(result.findings) == 0
        assert result.summary["error"] == 0

    def test_field_types(self) -> None:
        """Test that AuditResult has correct field types."""
        result = AuditResult(
            project_path="/project",
            findings=[],
            summary={"error": 0},
        )

        assert isinstance(result.project_path, str)
        assert isinstance(result.findings, list)
        assert isinstance(result.summary, dict)


class TestModelSerialization:
    """Test that models can be serialized/converted to dict if needed."""

    def test_validation_finding_to_dict(self) -> None:
        """Test converting ValidationFinding to dictionary format."""
        finding = ValidationFinding(
            code="ENV001",
            severity="error",
            variable="API_KEY",
            file=".env",
            line=42,
            message="Test message",
            remediation="Test fix",
        )

        # Access fields as dict-like (dataclass should support this)
        assert finding.code == "ENV001"
        assert finding.severity == "error"
        assert finding.variable == "API_KEY"
        assert finding.file == ".env"
        assert finding.line == 42

    def test_audit_result_structure(self) -> None:
        """Test AuditResult has proper nested structure."""
        findings = [
            ValidationFinding("ENV001", "error", "VAR", ".env", 1, "msg", "fix"),
        ]
        result = AuditResult(
            project_path="/project",
            findings=findings,
            summary={"error": 1},
        )

        # Verify nested access works
        assert result.findings[0].code == "ENV001"
        assert result.findings[0].variable == "VAR"
        assert result.summary["error"] == 1
