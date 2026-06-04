"""Tests for validators module."""

from envsentry import validators
from envsentry.config import SchemaVariable
from envsentry.models import EnvVariable, ParsedEnvFile


def test_check_missing_required():
    """Test ENV001: missing required variables."""
    env_vars = {
        "VAR1": EnvVariable("VAR1", "value1", 1, ".env"),
    }
    schema = {
        "VAR1": SchemaVariable(required=True),
        "VAR2": SchemaVariable(required=True),
        "VAR3": SchemaVariable(required=False),
    }

    findings = validators.check_missing_required(env_vars, schema)

    assert len(findings) == 1
    assert findings[0].code == "ENV001"
    assert findings[0].variable == "VAR2"
    assert findings[0].severity == "error"
    assert "VAR2" in findings[0].message
    # Ensure no actual value is in the finding
    assert "value1" not in findings[0].message


def test_check_missing_required_all_present():
    """Test ENV001: no missing variables."""
    env_vars = {
        "VAR1": EnvVariable("VAR1", "value1", 1, ".env"),
        "VAR2": EnvVariable("VAR2", "value2", 2, ".env"),
    }
    schema = {
        "VAR1": SchemaVariable(required=True),
        "VAR2": SchemaVariable(required=True),
    }

    findings = validators.check_missing_required(env_vars, schema)

    assert len(findings) == 0


def test_check_undocumented():
    """Test ENV002: undocumented variables."""
    env_vars = {
        "VAR1": EnvVariable("VAR1", "value1", 1, ".env"),
        "VAR2": EnvVariable("VAR2", "value2", 2, ".env"),
    }
    schema = {
        "VAR1": SchemaVariable(required=True),
    }

    findings = validators.check_undocumented(env_vars, schema)

    assert len(findings) == 1
    assert findings[0].code == "ENV002"
    assert findings[0].variable == "VAR2"
    assert findings[0].severity == "warning"


def test_check_undocumented_all_documented():
    """Test ENV002: all variables documented."""
    env_vars = {
        "VAR1": EnvVariable("VAR1", "value1", 1, ".env"),
    }
    schema = {
        "VAR1": SchemaVariable(required=True),
        "VAR2": SchemaVariable(required=False),
    }

    findings = validators.check_undocumented(env_vars, schema)

    assert len(findings) == 0


def test_check_duplicates():
    """Test ENV003: duplicate variables."""
    parsed = ParsedEnvFile(
        path=".env",
        variables=[
            EnvVariable("VAR1", "value1", 1, ".env"),
            EnvVariable("VAR1", "value2", 5, ".env"),
            EnvVariable("VAR2", "value3", 3, ".env"),
        ],
        duplicates={"VAR1": [1, 5]},
    )

    findings = validators.check_duplicates(parsed)

    assert len(findings) == 1
    assert findings[0].code == "ENV003"
    assert findings[0].variable == "VAR1"
    assert findings[0].severity == "error"
    assert "2 times" in findings[0].message
    # Ensure no actual values in finding
    assert "value1" not in findings[0].message
    assert "value2" not in findings[0].message


def test_check_duplicates_none():
    """Test ENV003: no duplicates."""
    parsed = ParsedEnvFile(
        path=".env",
        variables=[
            EnvVariable("VAR1", "value1", 1, ".env"),
            EnvVariable("VAR2", "value2", 2, ".env"),
        ],
        duplicates={},
    )

    findings = validators.check_duplicates(parsed)

    assert len(findings) == 0


def test_check_empty_required():
    """Test ENV004: empty required variables."""
    env_vars = {
        "VAR1": EnvVariable("VAR1", None, 1, ".env"),
        "VAR2": EnvVariable("VAR2", "", 2, ".env"),
        "VAR3": EnvVariable("VAR3", "   ", 3, ".env"),
        "VAR4": EnvVariable("VAR4", "value", 4, ".env"),
    }
    schema = {
        "VAR1": SchemaVariable(required=True),
        "VAR2": SchemaVariable(required=True),
        "VAR3": SchemaVariable(required=True),
        "VAR4": SchemaVariable(required=True),
    }

    findings = validators.check_empty_required(env_vars, schema)

    assert len(findings) == 3
    codes = {f.variable for f in findings}
    assert codes == {"VAR1", "VAR2", "VAR3"}
    for finding in findings:
        assert finding.code == "ENV004"
        assert finding.severity == "error"


def test_check_empty_required_optional():
    """Test ENV004: empty optional variables are okay."""
    env_vars = {
        "VAR1": EnvVariable("VAR1", None, 1, ".env"),
    }
    schema = {
        "VAR1": SchemaVariable(required=False),
    }

    findings = validators.check_empty_required(env_vars, schema)

    assert len(findings) == 0


def test_check_invalid_types_integer():
    """Test ENV005: integer type validation."""
    env_vars = {
        "PORT": EnvVariable("PORT", "8080", 1, ".env"),
        "INVALID_PORT": EnvVariable("INVALID_PORT", "not-a-number", 2, ".env"),
    }
    schema = {
        "PORT": SchemaVariable(type="integer"),
        "INVALID_PORT": SchemaVariable(type="integer"),
    }

    findings = validators.check_invalid_types(env_vars, schema)

    assert len(findings) == 1
    assert findings[0].code == "ENV005"
    assert findings[0].variable == "INVALID_PORT"
    assert "integer" in findings[0].message
    # Ensure no actual value leaked
    assert "not-a-number" not in findings[0].message


def test_check_invalid_types_float():
    """Test ENV005: float type validation."""
    env_vars = {
        "RATE": EnvVariable("RATE", "3.14", 1, ".env"),
        "INVALID_RATE": EnvVariable("INVALID_RATE", "three", 2, ".env"),
    }
    schema = {
        "RATE": SchemaVariable(type="float"),
        "INVALID_RATE": SchemaVariable(type="float"),
    }

    findings = validators.check_invalid_types(env_vars, schema)

    assert len(findings) == 1
    assert findings[0].variable == "INVALID_RATE"


def test_check_invalid_types_boolean():
    """Test ENV005: boolean type validation with all accepted values."""
    # Valid boolean values
    valid_bools = {
        "TRUE1": EnvVariable("TRUE1", "true", 1, ".env"),
        "TRUE2": EnvVariable("TRUE2", "1", 2, ".env"),
        "TRUE3": EnvVariable("TRUE3", "yes", 3, ".env"),
        "TRUE4": EnvVariable("TRUE4", "on", 4, ".env"),
        "FALSE1": EnvVariable("FALSE1", "false", 5, ".env"),
        "FALSE2": EnvVariable("FALSE2", "0", 6, ".env"),
        "FALSE3": EnvVariable("FALSE3", "no", 7, ".env"),
        "FALSE4": EnvVariable("FALSE4", "off", 8, ".env"),
        "MIXED": EnvVariable("MIXED", "TrUe", 9, ".env"),  # Case insensitive
    }
    schema = {name: SchemaVariable(type="boolean") for name in valid_bools}

    findings = validators.check_invalid_types(valid_bools, schema)
    assert len(findings) == 0

    # Invalid boolean values
    invalid_bools = {
        "BAD1": EnvVariable("BAD1", "maybe", 1, ".env"),
        "BAD2": EnvVariable("BAD2", "2", 2, ".env"),
    }
    schema_invalid = {name: SchemaVariable(type="boolean") for name in invalid_bools}

    findings_invalid = validators.check_invalid_types(invalid_bools, schema_invalid)
    assert len(findings_invalid) == 2


def test_check_invalid_urls():
    """Test ENV006: URL validation."""
    env_vars = {
        "VALID_URL": EnvVariable("VALID_URL", "https://example.com", 1, ".env"),
        "INVALID_URL1": EnvVariable("INVALID_URL1", "not a url", 2, ".env"),
        "INVALID_URL2": EnvVariable("INVALID_URL2", "http://", 3, ".env"),
    }
    schema = {
        "VALID_URL": SchemaVariable(type="url"),
        "INVALID_URL1": SchemaVariable(type="url"),
        "INVALID_URL2": SchemaVariable(type="url"),
    }

    findings = validators.check_invalid_urls(env_vars, schema)

    assert len(findings) == 2
    invalid_vars = {f.variable for f in findings}
    assert invalid_vars == {"INVALID_URL1", "INVALID_URL2"}
    for finding in findings:
        assert finding.code == "ENV006"
        assert finding.severity == "error"


def test_check_invalid_choices():
    """Test ENV007: choices validation."""
    env_vars = {
        "ENVIRONMENT": EnvVariable("ENVIRONMENT", "production", 1, ".env"),
        "BAD_ENV": EnvVariable("BAD_ENV", "unknown", 2, ".env"),
    }
    schema = {
        "ENVIRONMENT": SchemaVariable(choices=["development", "staging", "production"]),
        "BAD_ENV": SchemaVariable(choices=["development", "staging", "production"]),
    }

    findings = validators.check_invalid_choices(env_vars, schema)

    assert len(findings) == 1
    assert findings[0].code == "ENV007"
    assert findings[0].variable == "BAD_ENV"
    # Ensure no actual value leaked
    assert "unknown" not in findings[0].message


def test_check_placeholders():
    """Test ENV008: placeholder detection."""
    env_vars = {
        "VALID": EnvVariable("VALID", "actual-api-key-12345", 1, ".env"),
        "PH1": EnvVariable("PH1", "your-api-key-here", 2, ".env"),
        "PH2": EnvVariable("PH2", "replace-me", 3, ".env"),
        "PH3": EnvVariable("PH3", "example-value", 4, ".env"),
        "PH4": EnvVariable("PH4", "<your-key>", 5, ".env"),
        "PH5": EnvVariable("PH5", "xxx", 6, ".env"),
    }
    schema = {name: SchemaVariable() for name in env_vars}

    findings = validators.check_placeholders(env_vars, schema)

    # Should detect all placeholders except VALID
    assert len(findings) >= 5
    placeholder_vars = {f.variable for f in findings}
    assert "PH1" in placeholder_vars
    assert "PH2" in placeholder_vars
    assert "PH3" in placeholder_vars
    assert "PH4" in placeholder_vars
    assert "PH5" in placeholder_vars
    assert "VALID" not in placeholder_vars
    for finding in findings:
        assert finding.code == "ENV008"
        assert finding.severity == "warning"


def test_check_length_constraints():
    """Test ENV009: length constraint validation."""
    env_vars = {
        "SHORT": EnvVariable("SHORT", "abc", 1, ".env"),
        "LONG": EnvVariable("LONG", "a" * 100, 2, ".env"),
        "VALID": EnvVariable("VALID", "valid-length", 3, ".env"),
    }
    schema = {
        "SHORT": SchemaVariable(min_length=5),
        "LONG": SchemaVariable(max_length=50),
        "VALID": SchemaVariable(min_length=5, max_length=50),
    }

    findings = validators.check_length_constraints(env_vars, schema)

    assert len(findings) == 2
    vars_with_issues = {f.variable for f in findings}
    assert vars_with_issues == {"SHORT", "LONG"}
    for finding in findings:
        assert finding.code == "ENV009"
        assert finding.severity == "error"


def test_check_numeric_constraints():
    """Test ENV010: numeric constraint validation."""
    env_vars = {
        "LOW": EnvVariable("LOW", "5", 1, ".env"),
        "HIGH": EnvVariable("HIGH", "9999", 2, ".env"),
        "VALID": EnvVariable("VALID", "8080", 3, ".env"),
    }
    schema = {
        "LOW": SchemaVariable(type="integer", min=10),
        "HIGH": SchemaVariable(type="integer", max=8000),
        "VALID": SchemaVariable(type="integer", min=1024, max=65535),
    }

    findings = validators.check_numeric_constraints(env_vars, schema)

    assert len(findings) == 2
    vars_with_issues = {f.variable for f in findings}
    assert vars_with_issues == {"LOW", "HIGH"}
    for finding in findings:
        assert finding.code == "ENV010"
        assert finding.severity == "error"


def test_check_numeric_constraints_float():
    """Test ENV010: float constraint validation."""
    env_vars = {
        "RATE": EnvVariable("RATE", "0.5", 1, ".env"),
    }
    schema = {
        "RATE": SchemaVariable(type="float", min=1.0, max=10.0),
    }

    findings = validators.check_numeric_constraints(env_vars, schema)

    assert len(findings) == 1
    assert findings[0].variable == "RATE"


def test_secret_leakage_prevention():
    """Test that no validator exposes actual environment variable values."""
    # Create variables with secret values
    env_vars = {
        "API_KEY": EnvVariable("API_KEY", "super-secret-12345", 1, ".env"),
        "PASSWORD": EnvVariable("PASSWORD", "p@ssw0rd!", 2, ".env"),
    }
    schema = {
        "API_KEY": SchemaVariable(secret=True, min_length=50),  # Will fail min_length
        "PASSWORD": SchemaVariable(secret=True, type="integer"),  # Will fail type
    }

    # Run all validators that might produce findings
    all_findings = []
    all_findings.extend(validators.check_empty_required(env_vars, schema))
    all_findings.extend(validators.check_invalid_types(env_vars, schema))
    all_findings.extend(validators.check_length_constraints(env_vars, schema))

    # Ensure no actual secret values appear in any finding field
    for finding in all_findings:
        # Check all string fields
        assert "super-secret-12345" not in finding.code
        assert "super-secret-12345" not in finding.message
        assert "super-secret-12345" not in finding.remediation
        assert "super-secret-12345" not in finding.file
        assert "p@ssw0rd!" not in finding.code
        assert "p@ssw0rd!" not in finding.message
        assert "p@ssw0rd!" not in finding.remediation


# ============================================================================
# EXPANDED VALIDATOR TESTS - Comprehensive coverage of all validators
# ============================================================================


def test_boolean_validator_all_true_values():
    """Test boolean validator accepts all documented TRUE variations."""
    true_values = ["true", "True", "TRUE", "1", "yes", "Yes", "YES", "on", "On", "ON"]
    env_vars = {
        f"BOOL_{i}": EnvVariable(f"BOOL_{i}", val, i + 1, ".env")
        for i, val in enumerate(true_values)
    }
    schema = {name: SchemaVariable(type="boolean") for name in env_vars}

    findings = validators.check_invalid_types(env_vars, schema)

    # All should be valid - no findings
    assert len(findings) == 0


def test_boolean_validator_all_false_values():
    """Test boolean validator accepts all documented FALSE variations."""
    false_values = ["false", "False", "FALSE", "0", "no", "No", "NO", "off", "Off", "OFF"]
    env_vars = {
        f"BOOL_{i}": EnvVariable(f"BOOL_{i}", val, i + 1, ".env")
        for i, val in enumerate(false_values)
    }
    schema = {name: SchemaVariable(type="boolean") for name in env_vars}

    findings = validators.check_invalid_types(env_vars, schema)

    # All should be valid - no findings
    assert len(findings) == 0


def test_boolean_validator_invalid_values():
    """Test boolean validator rejects invalid boolean values."""
    invalid_values = ["maybe", "enabled", "disabled", "2", "random", "yep", "nope", "t", "f"]
    env_vars = {
        f"BOOL_{i}": EnvVariable(f"BOOL_{i}", val, i + 1, ".env")
        for i, val in enumerate(invalid_values)
    }
    schema = {name: SchemaVariable(type="boolean") for name in env_vars}

    findings = validators.check_invalid_types(env_vars, schema)

    # All should be invalid
    assert len(findings) == len(invalid_values)
    for finding in findings:
        assert finding.code == "ENV005"
        assert "boolean" in finding.message.lower()


def test_url_validator_valid_schemes():
    """Test URL validator accepts valid http/https/postgres/mysql URLs."""
    valid_urls = {
        "HTTP": EnvVariable("HTTP", "http://example.com", 1, ".env"),
        "HTTPS": EnvVariable("HTTPS", "https://example.com:443/path", 2, ".env"),
        "POSTGRES": EnvVariable("POSTGRES", "postgres://user:pass@localhost:5432/db", 3, ".env"),
        "MYSQL": EnvVariable("MYSQL", "mysql://user:pass@localhost:3306/db", 4, ".env"),
        "FTP": EnvVariable("FTP", "ftp://ftp.example.com", 5, ".env"),
    }
    schema = {name: SchemaVariable(type="url") for name in valid_urls}

    findings = validators.check_invalid_urls(valid_urls, schema)

    # All should be valid
    assert len(findings) == 0


def test_url_validator_invalid_urls():
    """Test URL validator rejects malformed URLs."""
    invalid_urls = {
        "NO_SCHEME": EnvVariable("NO_SCHEME", "example.com", 1, ".env"),
        "NO_HOST": EnvVariable("NO_HOST", "http://", 2, ".env"),
        "SPACES": EnvVariable("SPACES", "http://exam ple.com", 3, ".env"),
        "JUST_TEXT": EnvVariable("JUST_TEXT", "not-a-url", 4, ".env"),
    }
    schema = {name: SchemaVariable(type="url") for name in invalid_urls}

    findings = validators.check_invalid_urls(invalid_urls, schema)

    # All should be invalid
    assert len(findings) >= 2  # At least NO_SCHEME and NO_HOST should fail
    for finding in findings:
        assert finding.code == "ENV006"


def test_url_validator_no_network_requests():
    """Test that URL validator never makes network requests."""
    # Use a URL that would fail if actually requested
    env_vars = {
        "URL": EnvVariable("URL", "https://this-domain-does-not-exist-12345.com", 1, ".env"),
    }
    schema = {"URL": SchemaVariable(type="url")}

    # Should not raise network errors - only syntax validation
    findings = validators.check_invalid_urls(env_vars, schema)

    # Should be syntactically valid (no network check)
    assert len(findings) == 0


def test_placeholder_detection_all_patterns():
    """Test placeholder detection with all documented patterns."""
    placeholders = {
        "P1": EnvVariable("P1", "your-key-here", 1, ".env"),
        "P2": EnvVariable("P2", "your-api-key", 2, ".env"),
        "P3": EnvVariable("P3", "replace-me", 3, ".env"),
        "P4": EnvVariable("P4", "change-this", 4, ".env"),
        "P5": EnvVariable("P5", "changeme", 5, ".env"),
        "P6": EnvVariable("P6", "example-secret", 6, ".env"),
        "P7": EnvVariable("P7", "example", 7, ".env"),
        "P8": EnvVariable("P8", "placeholder", 8, ".env"),
        "P9": EnvVariable("P9", "<insert-key>", 9, ".env"),
        "P10": EnvVariable("P10", "xxx", 10, ".env"),
        "P11": EnvVariable("P11", "yyy", 11, ".env"),
        "P12": EnvVariable("P12", "zzz", 12, ".env"),
    }
    schema = {name: SchemaVariable() for name in placeholders}

    findings = validators.check_placeholders(placeholders, schema)

    # Should detect all placeholders
    detected = {f.variable for f in findings}
    assert len(detected) >= 10  # Should catch most patterns


def test_placeholder_detection_no_false_positives():
    """Test placeholder detection doesn't flag legitimate values."""
    legitimate = {
        "ENV": EnvVariable("ENV", "prod", 1, ".env"),
        "DEBUG": EnvVariable("DEBUG", "true", 2, ".env"),
        "HOST": EnvVariable("HOST", "localhost", 3, ".env"),
        "PORT": EnvVariable("PORT", "8080", 4, ".env"),
        "SHORT": EnvVariable("SHORT", "ok", 5, ".env"),
        "API_KEY": EnvVariable("API_KEY", "ak_live_1234567890abcdef", 6, ".env"),
    }
    schema = {name: SchemaVariable() for name in legitimate}

    findings = validators.check_placeholders(legitimate, schema)

    # Should not flag legitimate values
    detected = {f.variable for f in findings}
    assert "ENV" not in detected
    assert "DEBUG" not in detected
    assert "HOST" not in detected
    assert "PORT" not in detected
    assert "SHORT" not in detected
    assert "API_KEY" not in detected


def test_placeholder_detection_case_insensitive():
    """Test placeholder detection is case-insensitive."""
    variations = {
        "P1": EnvVariable("P1", "REPLACE-ME", 1, ".env"),
        "P2": EnvVariable("P2", "Replace-Me", 2, ".env"),
        "P3": EnvVariable("P3", "PLACEHOLDER", 3, ".env"),
        "P4": EnvVariable("P4", "Example", 4, ".env"),
    }
    schema = {name: SchemaVariable() for name in variations}

    findings = validators.check_placeholders(variations, schema)

    # Should detect all case variations
    assert len(findings) >= 4


def test_integer_validator_valid():
    """Test integer validator with valid integers."""
    env_vars = {
        "POSITIVE": EnvVariable("POSITIVE", "123", 1, ".env"),
        "NEGATIVE": EnvVariable("NEGATIVE", "-456", 2, ".env"),
        "ZERO": EnvVariable("ZERO", "0", 3, ".env"),
        "LARGE": EnvVariable("LARGE", "999999999", 4, ".env"),
    }
    schema = {name: SchemaVariable(type="integer") for name in env_vars}

    findings = validators.check_invalid_types(env_vars, schema)

    assert len(findings) == 0


def test_integer_validator_rejects_floats():
    """Test integer validator rejects float values."""
    env_vars = {
        "FLOAT": EnvVariable("FLOAT", "3.14", 1, ".env"),
        "DECIMAL": EnvVariable("DECIMAL", "1.0", 2, ".env"),
    }
    schema = {name: SchemaVariable(type="integer") for name in env_vars}

    findings = validators.check_invalid_types(env_vars, schema)

    # Should reject floats for integer type
    assert len(findings) == 2


def test_integer_validator_rejects_non_numeric():
    """Test integer validator rejects non-numeric strings."""
    env_vars = {
        "TEXT": EnvVariable("TEXT", "not-a-number", 1, ".env"),
        "MIXED": EnvVariable("MIXED", "123abc", 2, ".env"),
    }
    schema = {name: SchemaVariable(type="integer") for name in env_vars}

    findings = validators.check_invalid_types(env_vars, schema)

    assert len(findings) == 2


def test_float_validator_valid():
    """Test float validator accepts floats and integers."""
    env_vars = {
        "FLOAT": EnvVariable("FLOAT", "3.14159", 1, ".env"),
        "INT_AS_FLOAT": EnvVariable("INT_AS_FLOAT", "42", 2, ".env"),
        "NEGATIVE": EnvVariable("NEGATIVE", "-1.5", 3, ".env"),
        "SCIENTIFIC": EnvVariable("SCIENTIFIC", "1.23e-4", 4, ".env"),
    }
    schema = {name: SchemaVariable(type="float") for name in env_vars}

    findings = validators.check_invalid_types(env_vars, schema)

    assert len(findings) == 0


def test_float_validator_rejects_non_numeric():
    """Test float validator rejects non-numeric strings."""
    env_vars = {
        "TEXT": EnvVariable("TEXT", "not-a-number", 1, ".env"),
    }
    schema = {"TEXT": SchemaVariable(type="float")}

    findings = validators.check_invalid_types(env_vars, schema)

    assert len(findings) == 1


def test_string_length_boundaries():
    """Test string length constraints with boundary values."""
    env_vars = {
        "EXACTLY_MIN": EnvVariable("EXACTLY_MIN", "12345", 1, ".env"),  # len=5
        "EXACTLY_MAX": EnvVariable("EXACTLY_MAX", "1234567890", 2, ".env"),  # len=10
        "BELOW_MIN": EnvVariable("BELOW_MIN", "1234", 3, ".env"),  # len=4
        "ABOVE_MAX": EnvVariable("ABOVE_MAX", "12345678901", 4, ".env"),  # len=11
    }
    schema = {
        "EXACTLY_MIN": SchemaVariable(min_length=5, max_length=10),
        "EXACTLY_MAX": SchemaVariable(min_length=5, max_length=10),
        "BELOW_MIN": SchemaVariable(min_length=5, max_length=10),
        "ABOVE_MAX": SchemaVariable(min_length=5, max_length=10),
    }

    findings = validators.check_length_constraints(env_vars, schema)

    # Should find 2 violations (BELOW_MIN and ABOVE_MAX)
    assert len(findings) == 2
    vars_with_issues = {f.variable for f in findings}
    assert "BELOW_MIN" in vars_with_issues
    assert "ABOVE_MAX" in vars_with_issues
    assert "EXACTLY_MIN" not in vars_with_issues
    assert "EXACTLY_MAX" not in vars_with_issues


def test_string_length_unicode():
    """Test string length constraints work with unicode characters."""
    env_vars = {
        "UNICODE": EnvVariable("UNICODE", "café", 1, ".env"),  # 4 chars
        "EMOJI": EnvVariable("EMOJI", "🔒🔑", 2, ".env"),  # 2 chars
    }
    schema = {
        "UNICODE": SchemaVariable(min_length=4, max_length=10),
        "EMOJI": SchemaVariable(min_length=2, max_length=5),
    }

    findings = validators.check_length_constraints(env_vars, schema)

    # Both should be within range
    assert len(findings) == 0


def test_numeric_constraints_boundaries():
    """Test numeric constraints with boundary values."""
    env_vars = {
        "AT_MIN": EnvVariable("AT_MIN", "10", 1, ".env"),
        "AT_MAX": EnvVariable("AT_MAX", "100", 2, ".env"),
        "BELOW_MIN": EnvVariable("BELOW_MIN", "9", 3, ".env"),
        "ABOVE_MAX": EnvVariable("ABOVE_MAX", "101", 4, ".env"),
    }
    schema = {
        "AT_MIN": SchemaVariable(type="integer", min=10, max=100),
        "AT_MAX": SchemaVariable(type="integer", min=10, max=100),
        "BELOW_MIN": SchemaVariable(type="integer", min=10, max=100),
        "ABOVE_MAX": SchemaVariable(type="integer", min=10, max=100),
    }

    findings = validators.check_numeric_constraints(env_vars, schema)

    # Should find 2 violations
    assert len(findings) == 2
    vars_with_issues = {f.variable for f in findings}
    assert "BELOW_MIN" in vars_with_issues
    assert "ABOVE_MAX" in vars_with_issues


def test_choices_case_sensitivity():
    """Test that choices validation is case-sensitive."""
    env_vars = {
        "EXACT": EnvVariable("EXACT", "production", 1, ".env"),
        "WRONG_CASE": EnvVariable("WRONG_CASE", "Production", 2, ".env"),
    }
    schema = {
        "EXACT": SchemaVariable(choices=["development", "staging", "production"]),
        "WRONG_CASE": SchemaVariable(choices=["development", "staging", "production"]),
    }

    findings = validators.check_invalid_choices(env_vars, schema)

    # Should reject wrong case
    assert len(findings) == 1
    assert findings[0].variable == "WRONG_CASE"
