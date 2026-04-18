"""Tests for config module."""

from pathlib import Path
import pytest

from envsentry.config import load_config, infer_schema_from_example, SchemaVariable
from envsentry.models import EnvVariable, ParsedEnvFile


def test_load_config_nonexistent(tmp_path):
    """Test loading config when file doesn't exist."""
    config_path = tmp_path / "nonexistent.toml"
    with pytest.raises(FileNotFoundError):
        load_config(config_path)


def test_load_config_none():
    """Test loading config with None path."""
    result = load_config(None)
    assert result == {}


def test_load_config_basic(tmp_path):
    """Test loading basic config with required variable."""
    config_path = tmp_path / ".envsentry.toml"
    config_path.write_text("""
[variables.DATABASE_URL]
required = true
type = "url"
secret = true
""")

    schema = load_config(config_path)

    assert "DATABASE_URL" in schema
    var = schema["DATABASE_URL"]
    assert var.required is True
    assert var.type == "url"
    assert var.secret is True


def test_load_config_all_constraints(tmp_path):
    """Test loading config with all constraint types."""
    config_path = tmp_path / ".envsentry.toml"
    config_path.write_text("""
[variables.API_KEY]
required = true
type = "string"
secret = true
min_length = 20
max_length = 100

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

    schema = load_config(config_path)

    # Check API_KEY
    assert "API_KEY" in schema
    api_key = schema["API_KEY"]
    assert api_key.required is True
    assert api_key.secret is True
    assert api_key.min_length == 20
    assert api_key.max_length == 100

    # Check PORT
    assert "PORT" in schema
    port = schema["PORT"]
    assert port.required is False
    assert port.type == "integer"
    assert port.min == 1024
    assert port.max == 65535

    # Check ENVIRONMENT
    assert "ENVIRONMENT" in schema
    env = schema["ENVIRONMENT"]
    assert env.choices == ["development", "staging", "production"]


def test_load_config_defaults(tmp_path):
    """Test that config uses correct defaults."""
    config_path = tmp_path / ".envsentry.toml"
    config_path.write_text("""
[variables.SIMPLE_VAR]
""")

    schema = load_config(config_path)

    var = schema["SIMPLE_VAR"]
    assert var.required is True  # Default
    assert var.type == "string"  # Default
    assert var.secret is False  # Default
    assert var.min_length is None
    assert var.max_length is None


def test_load_config_invalid_toml(tmp_path):
    """Test loading invalid TOML."""
    config_path = tmp_path / ".envsentry.toml"
    config_path.write_text("""
[variables.BAD
this is not valid TOML
""")

    with pytest.raises(ValueError, match="Invalid TOML"):
        load_config(config_path)


def test_load_config_unknown_property(tmp_path):
    """Test loading config with unknown property."""
    config_path = tmp_path / ".envsentry.toml"
    config_path.write_text("""
[variables.VAR1]
required = true
unknown_property = "value"
""")

    with pytest.raises(ValueError, match="Unknown properties"):
        load_config(config_path)


def test_load_config_invalid_variables_section(tmp_path):
    """Test loading config with non-table variables section."""
    config_path = tmp_path / ".envsentry.toml"
    config_path.write_text("""
variables = "not a table"
""")

    with pytest.raises(ValueError, match="must be a table"):
        load_config(config_path)


def test_infer_schema_from_example():
    """Test inferring schema from .env.example file."""
    parsed = ParsedEnvFile(
        path="/path/to/.env.example",
        variables=[
            EnvVariable(name="VAR1", value="example1", line_number=1, file="/path/to/.env.example"),
            EnvVariable(name="VAR2", value="example2", line_number=2, file="/path/to/.env.example"),
            EnvVariable(name="VAR3", value=None, line_number=3, file="/path/to/.env.example"),
        ],
    )

    schema = infer_schema_from_example(parsed)

    assert len(schema) == 3
    assert "VAR1" in schema
    assert "VAR2" in schema
    assert "VAR3" in schema

    # All should be required strings
    for var_name, var_schema in schema.items():
        assert var_schema.required is True
        assert var_schema.type == "string"
        assert var_schema.secret is False


def test_infer_schema_empty_example():
    """Test inferring schema from empty .env.example."""
    parsed = ParsedEnvFile(
        path="/path/to/.env.example",
        variables=[],
    )

    schema = infer_schema_from_example(parsed)

    assert schema == {}
