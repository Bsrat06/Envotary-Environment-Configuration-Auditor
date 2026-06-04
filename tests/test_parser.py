"""Tests for the dotenv parser module."""

from __future__ import annotations

from pathlib import Path

import pytest

from envotary.parser import ParseError, parse_dotenv_file


def test_parse_basic_key_value(tmp_path: Path) -> None:
    """Test parsing basic KEY=value pairs."""
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgresql://localhost/mydb\n")

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 1
    assert result.variables[0].name == "DATABASE_URL"
    assert result.variables[0].value == "postgresql://localhost/mydb"
    assert result.variables[0].line_number == 1
    assert result.variables[0].file == str(env_file.absolute())
    assert len(result.duplicates) == 0


def test_parse_multiple_variables(tmp_path: Path) -> None:
    """Test parsing multiple environment variables."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "API_KEY=abc123\n"
        "SECRET=mysecret\n"
        "PORT=8080\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 3
    assert result.variables[0].name == "API_KEY"
    assert result.variables[1].name == "SECRET"
    assert result.variables[2].name == "PORT"


def test_parse_double_quoted_values(tmp_path: Path) -> None:
    """Test parsing double-quoted values."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        'MESSAGE="Hello World"\n'
        'PATH="/usr/local/bin"\n'
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 2
    assert result.variables[0].name == "MESSAGE"
    assert result.variables[0].value == "Hello World"
    assert result.variables[1].name == "PATH"
    assert result.variables[1].value == "/usr/local/bin"


def test_parse_single_quoted_values(tmp_path: Path) -> None:
    """Test parsing single-quoted values."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "MESSAGE='Hello World'\n"
        "PATH='/usr/local/bin'\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 2
    assert result.variables[0].name == "MESSAGE"
    assert result.variables[0].value == "Hello World"
    assert result.variables[1].name == "PATH"
    assert result.variables[1].value == "/usr/local/bin"


def test_parse_comments(tmp_path: Path) -> None:
    """Test that comments are ignored."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# This is a comment\n"
        "API_KEY=abc123\n"
        "# Another comment\n"
        "SECRET=mysecret\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 2
    assert result.variables[0].name == "API_KEY"
    assert result.variables[1].name == "SECRET"


def test_parse_empty_lines(tmp_path: Path) -> None:
    """Test that empty lines are ignored."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "API_KEY=abc123\n"
        "\n"
        "SECRET=mysecret\n"
        "\n"
        "\n"
        "PORT=8080\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 3


def test_parse_whitespace_trimming(tmp_path: Path) -> None:
    """Test that whitespace around keys and values is trimmed."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "  API_KEY  =  abc123  \n"
        "\tSECRET\t=\tmysecret\t\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 2
    assert result.variables[0].name == "API_KEY"
    assert result.variables[0].value == "abc123"
    assert result.variables[1].name == "SECRET"
    assert result.variables[1].value == "mysecret"


def test_parse_empty_values(tmp_path: Path) -> None:
    """Test parsing keys with empty values."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "EMPTY_VAR=\n"
        "ALSO_EMPTY= \n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 2
    assert result.variables[0].name == "EMPTY_VAR"
    assert result.variables[0].value is None
    assert result.variables[1].name == "ALSO_EMPTY"
    assert result.variables[1].value is None


def test_parse_values_with_equals_sign(tmp_path: Path) -> None:
    """Test parsing values that contain = signs."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql://user:pass@host/db?param=value\n"
        "EQUATION=x=y+z\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 2
    assert result.variables[0].name == "DATABASE_URL"
    assert result.variables[0].value == "postgresql://user:pass@host/db?param=value"
    assert result.variables[1].name == "EQUATION"
    assert result.variables[1].value == "x=y+z"


def test_parse_duplicate_keys(tmp_path: Path) -> None:
    """Test detection of duplicate keys with line tracking."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "API_KEY=first_value\n"
        "SECRET=mysecret\n"
        "API_KEY=second_value\n"
        "PORT=8080\n"
        "API_KEY=third_value\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 5
    assert "API_KEY" in result.duplicates
    assert result.duplicates["API_KEY"] == [1, 3, 5]
    assert "SECRET" not in result.duplicates
    assert "PORT" not in result.duplicates


def test_parse_line_number_tracking(tmp_path: Path) -> None:
    """Test that line numbers are correctly tracked."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Comment on line 1\n"
        "VAR1=value1\n"
        "\n"
        "VAR2=value2\n"
        "# Another comment\n"
        "VAR3=value3\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 3
    assert result.variables[0].line_number == 2
    assert result.variables[1].line_number == 4
    assert result.variables[2].line_number == 6


def test_parse_missing_file(tmp_path: Path) -> None:
    """Test that FileNotFoundError is raised for missing files."""
    env_file = tmp_path / "nonexistent.env"

    with pytest.raises(FileNotFoundError):
        parse_dotenv_file(env_file)


def test_parse_directory_not_file(tmp_path: Path) -> None:
    """Test that ParseError is raised when path is a directory."""
    directory = tmp_path / "somedir"
    directory.mkdir()

    with pytest.raises(ParseError) as exc_info:
        parse_dotenv_file(directory)

    assert "not a file" in str(exc_info.value).lower()


def test_parse_various_key_formats(tmp_path: Path) -> None:
    """Test parsing keys with different valid formats."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SIMPLE=value\n"
        "WITH_UNDERSCORE=value\n"
        "WITH123NUMBERS=value\n"
        "MixedCase=value\n"
        "_LEADING_UNDERSCORE=value\n"
        "WITH-HYPHEN=value\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 6
    names = [v.name for v in result.variables]
    assert "SIMPLE" in names
    assert "WITH_UNDERSCORE" in names
    assert "WITH123NUMBERS" in names
    assert "MixedCase" in names
    assert "_LEADING_UNDERSCORE" in names
    assert "WITH-HYPHEN" in names


def test_parse_malformed_lines_are_skipped(tmp_path: Path) -> None:
    """Test that malformed lines that don't match KEY=value are skipped."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "VALID_KEY=value\n"
        "not a valid line\n"
        "ANOTHER_VALID=another\n"
        "=no_key\n"
        "123INVALID=value\n"
        "FINAL_VALID=final\n"
    )

    result = parse_dotenv_file(env_file)

    # Should only parse the valid KEY=value lines
    assert len(result.variables) == 3
    names = [v.name for v in result.variables]
    assert "VALID_KEY" in names
    assert "ANOTHER_VALID" in names
    assert "FINAL_VALID" in names


def test_parse_quoted_values_with_special_chars(tmp_path: Path) -> None:
    """Test parsing quoted values containing special characters."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        'MESSAGE="Hello, World! #special"\n'
        "PATH='/usr/bin:/usr/local/bin'\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 2
    assert result.variables[0].value == "Hello, World! #special"
    assert result.variables[1].value == "/usr/bin:/usr/local/bin"


def test_parse_unquoted_value_with_spaces(tmp_path: Path) -> None:
    """Test parsing unquoted values (spaces would be trimmed)."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "VALUE=unquoted value with spaces\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 1
    # Unquoted values are taken as-is after initial strip
    assert result.variables[0].value == "unquoted value with spaces"


def test_parse_empty_file(tmp_path: Path) -> None:
    """Test parsing an empty file."""
    env_file = tmp_path / ".env"
    env_file.write_text("")

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 0
    assert len(result.duplicates) == 0


def test_parse_only_comments(tmp_path: Path) -> None:
    """Test parsing a file with only comments."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Comment 1\n"
        "# Comment 2\n"
        "# Comment 3\n"
    )

    result = parse_dotenv_file(env_file)

    assert len(result.variables) == 0
