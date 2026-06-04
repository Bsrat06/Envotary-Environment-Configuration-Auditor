"""Tests for audit engine."""


from envsentry.engine import run_audit


def test_run_audit_no_files(tmp_path):
    """Test audit with no .env files present."""
    result = run_audit(tmp_path)

    assert result.project_path == str(tmp_path.resolve())
    assert len(result.findings) >= 1
    # Should report missing .env file
    assert any(f.code == "ENV_FILE_MISSING" for f in result.findings)


def test_run_audit_basic_success(tmp_path):
    """Test successful audit with valid configuration."""
    # Create .env file
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgres://localhost/test\nAPI_KEY=test-key-123\n")

    # Create .env.example
    example_file = tmp_path / ".env.example"
    example_file.write_text("DATABASE_URL=\nAPI_KEY=\n")

    result = run_audit(tmp_path)

    assert result.project_path == str(tmp_path.resolve())
    # Should have no errors for valid config
    assert result.summary.get("error", 0) == 0


def test_run_audit_missing_required(tmp_path):
    """Test audit detecting missing required variable."""
    # Create .env file missing a required var
    env_file = tmp_path / ".env"
    env_file.write_text("VAR1=value1\n")

    # Create .env.example defining two required vars
    example_file = tmp_path / ".env.example"
    example_file.write_text("VAR1=\nVAR2=\n")

    result = run_audit(tmp_path)

    # Should detect VAR2 is missing
    assert any(f.code == "ENV001" and f.variable == "VAR2" for f in result.findings)
    assert result.summary.get("error", 0) > 0


def test_run_audit_with_config_file(tmp_path):
    """Test audit using .envsentry.toml configuration."""
    # Create .env file
    env_file = tmp_path / ".env"
    env_file.write_text("PORT=8080\n")

    # Create config file
    config_file = tmp_path / ".envsentry.toml"
    config_file.write_text("""
[variables.PORT]
required = true
type = "integer"
min = 1024
max = 65535
""")

    result = run_audit(tmp_path)

    # Should pass validation
    assert result.summary.get("error", 0) == 0


def test_run_audit_type_error(tmp_path):
    """Test audit detecting type errors."""
    # Create .env file with invalid type
    env_file = tmp_path / ".env"
    env_file.write_text("PORT=not-a-number\n")

    # Create config file
    config_file = tmp_path / ".envsentry.toml"
    config_file.write_text("""
[variables.PORT]
type = "integer"
""")

    result = run_audit(tmp_path)

    # Should detect type error
    assert any(f.code == "ENV005" for f in result.findings)
    assert result.summary.get("error", 0) > 0


def test_run_audit_duplicates(tmp_path):
    """Test audit detecting duplicate variables."""
    # Create .env file with duplicates
    env_file = tmp_path / ".env"
    env_file.write_text("VAR1=value1\nVAR2=value2\nVAR1=value3\n")

    result = run_audit(tmp_path)

    # Should detect duplicate
    assert any(f.code == "ENV003" for f in result.findings)


def test_run_audit_parse_error(tmp_path):
    """Test audit handling parse errors gracefully."""
    # Create a file with binary content that will cause encoding error
    env_path = tmp_path / ".env"
    with open(env_path, "wb") as f:
        f.write(b"\x80\x81\x82\x83")  # Invalid UTF-8

    result = run_audit(tmp_path)

    # Should report parse error
    assert any(f.code == "PARSE_ERROR" for f in result.findings)


def test_run_audit_invalid_config(tmp_path):
    """Test audit handling invalid TOML config."""
    # Create valid .env
    env_file = tmp_path / ".env"
    env_file.write_text("VAR1=value1\n")

    # Create invalid config
    config_file = tmp_path / ".envsentry.toml"
    config_file.write_text("invalid toml content [[[\n")

    result = run_audit(tmp_path)

    # Should report config error
    assert any(f.code == "CONFIG_ERROR" for f in result.findings)


def test_run_audit_explicit_paths(tmp_path):
    """Test audit with explicit file paths."""
    # Create files in subdirectories
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    env_file = config_dir / "production.env"
    env_file.write_text("VAR1=value1\n")

    example_file = config_dir / "example.env"
    example_file.write_text("VAR1=\n")

    result = run_audit(tmp_path, env_file="config/production.env", example_file="config/example.env")

    assert result.project_path == str(tmp_path.resolve())
    # Should find and parse the explicit files
    assert result.summary.get("error", 0) == 0


def test_run_audit_comprehensive(tmp_path):
    """Test comprehensive audit with multiple issue types."""
    # Create .env with various issues
    env_file = tmp_path / ".env"
    env_file.write_text("""
PORT=not-a-number
DATABASE_URL=invalid-url
ENVIRONMENT=invalid-choice
API_KEY=replace-me
DUPLICATE=value1
DUPLICATE=value2
SHORT_VAR=ab
""")

    # Create config
    config_file = tmp_path / ".envsentry.toml"
    config_file.write_text("""
[variables.PORT]
type = "integer"

[variables.DATABASE_URL]
type = "url"

[variables.ENVIRONMENT]
choices = ["dev", "prod"]

[variables.API_KEY]
secret = true

[variables.SHORT_VAR]
min_length = 10

[variables.REQUIRED_VAR]
required = true
""")

    result = run_audit(tmp_path)

    # Should detect multiple issues
    codes = {f.code for f in result.findings}
    assert "ENV001" in codes  # missing REQUIRED_VAR
    assert "ENV003" in codes  # duplicate DUPLICATE
    assert "ENV005" in codes  # invalid type PORT
    assert "ENV006" in codes  # invalid URL
    assert "ENV007" in codes  # invalid choice
    assert "ENV008" in codes  # placeholder API_KEY
    assert "ENV009" in codes  # SHORT_VAR too short

    # Summary should have multiple errors
    assert result.summary.get("error", 0) > 0
    assert result.summary.get("warning", 0) > 0


def test_run_audit_summary_counts(tmp_path):
    """Test that summary counts are accurate."""
    # Create .env with known issues
    env_file = tmp_path / ".env"
    env_file.write_text("VAR1=your-value-here\n")  # Placeholder (warning)

    # Create example
    example_file = tmp_path / ".env.example"
    example_file.write_text("VAR1=\nVAR2=\n")  # VAR2 missing (error)

    result = run_audit(tmp_path)

    # Count findings by severity
    error_count = sum(1 for f in result.findings if f.severity == "error")
    warning_count = sum(1 for f in result.findings if f.severity == "warning")

    assert result.summary["error"] == error_count
    assert result.summary["warning"] == warning_count
