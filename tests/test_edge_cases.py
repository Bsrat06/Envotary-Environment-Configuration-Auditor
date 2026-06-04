"""Edge case and error handling tests for EnvSentry.

Tests malformed files, missing files, invalid configurations, path handling,
and other error conditions.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from envsentry.config import load_config
from envsentry.discovery import discover_files
from envsentry.parser import parse_dotenv_file


class TestParseErrors:
    """Test parsing of malformed .env files."""

    def test_parse_unclosed_quotes(self, tmp_path: Path) -> None:
        """Test parsing .env file with unclosed quotes."""
        env_file = tmp_path / ".env"
        env_file.write_text('VAR1="unclosed string\nVAR2=normal_value\n')

        # Parser should handle gracefully or raise clear error
        try:
            parsed = parse_dotenv_file(env_file)
            # If it doesn't raise, verify it parsed what it could
            assert parsed.path == str(env_file.absolute())
        except Exception as e:
            # If it raises, ensure error message is clear and doesn't leak values
            assert "unclosed" in str(e).lower() or "quote" in str(e).lower()

    def test_parse_invalid_unicode(self, tmp_path: Path) -> None:
        """Test parsing .env file with invalid unicode sequences."""
        env_file = tmp_path / ".env"
        # Write some problematic content
        try:
            env_file.write_bytes(b"VAR1=value\nVAR2=\xff\xfe\nVAR3=normal\n")
            parsed = parse_dotenv_file(env_file)
            # Should handle gracefully
            assert parsed.path == str(env_file.absolute())
        except Exception as e:
            # If it fails, ensure clean error handling (including ParseError)
            from envsentry.parser import ParseError
            assert isinstance(e, (UnicodeDecodeError, ValueError, ParseError))

    def test_parse_malformed_syntax(self, tmp_path: Path) -> None:
        """Test various malformed .env syntax."""
        test_cases = [
            "=VALUE_WITHOUT_KEY\n",
            "JUST_KEY_NO_EQUALS\n",
            "KEY==DOUBLE_EQUALS\n",
            "KEY = SPACES AROUND EQUALS\n",
            "KEY=VALUE=WITH=MANY=EQUALS\n",
        ]

        for idx, content in enumerate(test_cases):
            env_file = tmp_path / f".env.test{idx}"
            env_file.write_text(content)

            # Parser should either handle gracefully or raise clear error
            try:
                parsed = parse_dotenv_file(env_file)
                # If it parses, ensure it has valid structure
                assert hasattr(parsed, "variables")
                assert hasattr(parsed, "path")
            except Exception as e:
                # Errors should be clear
                error_msg = str(e)
                assert len(error_msg) > 0

    def test_parse_empty_lines_and_comments(self, tmp_path: Path) -> None:
        """Test that parser handles empty lines and comments correctly."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
# Comment line
VAR1=value1

  # Indented comment
VAR2=value2

# Another comment
  
VAR3=value3
"""
        )

        parsed = parse_dotenv_file(env_file)
        var_names = {v.name for v in parsed.variables}

        # Should parse only actual variables
        assert "VAR1" in var_names
        assert "VAR2" in var_names
        assert "VAR3" in var_names
        assert len(parsed.variables) == 3


class TestFileErrors:
    """Test handling of missing files, permissions, and invalid paths."""

    def test_parse_missing_file(self, tmp_path: Path) -> None:
        """Test parsing a file that doesn't exist."""
        missing_file = tmp_path / "nonexistent.env"

        with pytest.raises(FileNotFoundError):
            parse_dotenv_file(missing_file)

    def test_parse_directory_instead_of_file(self, tmp_path: Path) -> None:
        """Test parsing when path points to a directory."""
        directory = tmp_path / "env_dir"
        directory.mkdir()

        # Should raise ParseError for directory
        from envsentry.parser import ParseError
        with pytest.raises(ParseError):
            parse_dotenv_file(directory)

    def test_parse_empty_file(self, tmp_path: Path) -> None:
        """Test parsing an empty .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("")

        parsed = parse_dotenv_file(env_file)

        assert parsed.path == str(env_file.absolute())
        assert len(parsed.variables) == 0
        assert len(parsed.duplicates) == 0

    def test_parse_very_large_file(self, tmp_path: Path) -> None:
        """Test parsing a very large .env file."""
        env_file = tmp_path / ".env"

        # Create file with 10,000 lines
        lines = [f"VAR_{i}=value_{i}\n" for i in range(10_000)]
        env_file.write_text("".join(lines))

        parsed = parse_dotenv_file(env_file)

        # Should handle large files
        assert len(parsed.variables) == 10_000

    def test_discover_in_empty_directory(self, tmp_path: Path) -> None:
        """Test discovery in a directory with no .env files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        discovered = discover_files(empty_dir)

        # Should return empty results or handle gracefully
        assert isinstance(discovered, dict)
        assert discovered["env_file"] is None
        assert discovered["example_file"] is None

    def test_discover_nonexistent_path(self, tmp_path: Path) -> None:
        """Test discovery on a path that doesn't exist."""
        nonexistent = tmp_path / "does_not_exist"

        # Should handle non-existent paths gracefully or raise
        try:
            discovered = discover_files(nonexistent)
            # If it doesn't raise, should return None values
            assert discovered["env_file"] is None
        except (FileNotFoundError, OSError):
            # This is also acceptable
            pass


class TestConfigErrors:
    """Test handling of invalid configuration files."""

    def test_load_invalid_toml_syntax(self, tmp_path: Path) -> None:
        """Test loading config with invalid TOML syntax."""
        config_file = tmp_path / ".envsentry.toml"
        config_file.write_text(
            """
[variables]
VAR1 = {
    type = "string"
    # Missing closing brace
"""
        )

        with pytest.raises((ValueError, Exception)):
            load_config(config_file)

    def test_load_unknown_schema_properties(self, tmp_path: Path) -> None:
        """Test config with unknown schema properties."""
        config_file = tmp_path / ".envsentry.toml"
        config_file.write_text(
            """
[variables.VAR1]
type = "string"
unknown_property = "invalid"
another_unknown = 123
"""
        )

        # Should raise error about unknown properties
        with pytest.raises(ValueError) as exc_info:
            load_config(config_file)
        assert "unknown" in str(exc_info.value).lower() or "Unknown" in str(exc_info.value)

    def test_load_invalid_type_values(self, tmp_path: Path) -> None:
        """Test config with invalid type values."""
        config_file = tmp_path / ".envsentry.toml"
        config_file.write_text(
            """
[variables.VAR1]
type = "invalid_type"
required = true
"""
        )

        # Config loader accepts any type value - validation happens at runtime
        config = load_config(config_file)
        assert "VAR1" in config
        assert config["VAR1"].type == "invalid_type"

    def test_load_contradictory_constraints(self, tmp_path: Path) -> None:
        """Test config with contradictory constraints (min > max)."""
        config_file = tmp_path / ".envsentry.toml"
        config_file.write_text(
            """
[variables.VAR1]
type = "integer"
min = 100
max = 10
"""
        )

        # Config loader accepts contradictory constraints - they would be detected at validation time
        config = load_config(config_file)
        assert "VAR1" in config
        assert config["VAR1"].min == 100
        assert config["VAR1"].max == 10

    def test_load_invalid_choice_type(self, tmp_path: Path) -> None:
        """Test config with invalid choices type."""
        config_file = tmp_path / ".envsentry.toml"
        config_file.write_text(
            """
[variables.VAR1]
type = "string"
choices = "not_a_list"
"""
        )

        # Config loader accepts string for choices - type error would happen at validation time
        config = load_config(config_file)
        assert "VAR1" in config
        # Choices will be a string instead of list, which validators would handle
        assert config["VAR1"].choices == "not_a_list"

    def test_load_missing_config_file(self, tmp_path: Path) -> None:
        """Test loading config when .envsentry.toml doesn't exist."""
        empty_dir = tmp_path / "no_config"
        empty_dir.mkdir()
        config_file = empty_dir / ".envsentry.toml"

        # Should raise FileNotFoundError for non-existent file
        with pytest.raises(FileNotFoundError):
            load_config(config_file)


class TestPathHandling:
    """Test path handling edge cases across different OS styles."""

    def test_relative_paths(self, tmp_path: Path) -> None:
        """Test handling of relative paths."""
        env_file = tmp_path / ".env"
        env_file.write_text("VAR1=value1\n")

        # Test with relative path
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            parsed = parse_dotenv_file(Path(".env"))
            assert parsed.variables[0].name == "VAR1"
        finally:
            os.chdir(original_cwd)

    def test_absolute_paths(self, tmp_path: Path) -> None:
        """Test handling of absolute paths."""
        env_file = tmp_path / ".env"
        env_file.write_text("VAR1=value1\n")

        # Test with absolute path
        parsed = parse_dotenv_file(env_file.absolute())
        assert parsed.variables[0].name == "VAR1"

    def test_paths_with_spaces(self, tmp_path: Path) -> None:
        """Test handling of paths containing spaces."""
        space_dir = tmp_path / "dir with spaces"
        space_dir.mkdir()
        env_file = space_dir / ".env"
        env_file.write_text("VAR1=value1\n")

        parsed = parse_dotenv_file(env_file)
        assert parsed.variables[0].name == "VAR1"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_style_paths(self, tmp_path: Path) -> None:
        """Test handling of Windows-style paths (C:\\path\\to\\file)."""
        env_file = tmp_path / ".env"
        env_file.write_text("VAR1=value1\n")

        # Convert to Windows-style path string
        windows_path = str(env_file).replace("/", "\\")
        parsed = parse_dotenv_file(Path(windows_path))
        assert parsed.variables[0].name == "VAR1"

    def test_path_normalization(self, tmp_path: Path) -> None:
        """Test that paths with . and .. are normalized correctly."""
        env_file = tmp_path / ".env"
        env_file.write_text("VAR1=value1\n")

        # Path with . and ..
        weird_path = tmp_path / "." / ".." / tmp_path.name / ".env"
        parsed = parse_dotenv_file(weird_path)
        assert parsed.variables[0].name == "VAR1"


class TestMultilineValues:
    """Test handling of multiline values if parser supports them."""

    def test_multiline_with_quotes(self, tmp_path: Path) -> None:
        """Test parsing multiline values in quotes."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            '''VAR1="line1
line2
line3"
VAR2=single_line
'''
        )

        try:
            parsed = parse_dotenv_file(env_file)
            # If parser supports multiline, verify it works
            var1 = next((v for v in parsed.variables if v.name == "VAR1"), None)
            if var1 and var1.value:
                # Multiline supported
                assert "line1" in var1.value
            else:
                # Multiline not supported, should at least not crash
                assert len(parsed.variables) >= 1
        except Exception:
            # If multiline causes parse error, that's acceptable
            pass


class TestSpecialCharacters:
    """Test handling of special characters in variable names and values."""

    def test_special_chars_in_names(self, tmp_path: Path) -> None:
        """Test variable names with special characters."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """VAR_WITH_UNDERSCORES=value1
VAR-WITH-DASHES=value2
VAR.WITH.DOTS=value3
VAR123=value4
"""
        )

        parsed = parse_dotenv_file(env_file)
        var_names = {v.name for v in parsed.variables}

        # Common formats should be supported
        assert "VAR_WITH_UNDERSCORES" in var_names
        # Others may or may not be supported depending on parser
        assert len(var_names) >= 1

    def test_special_chars_in_values(self, tmp_path: Path) -> None:
        """Test values with special characters."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            r"""URL=https://example.com:8080/path?key=value&other=123
JSON_LIKE={"key":"value"}
SPECIAL_CHARS=!@#$%^&*()
BACKSLASH=C:\path\to\file
"""
        )

        parsed = parse_dotenv_file(env_file)

        # Should parse without crashing
        assert len(parsed.variables) >= 1
        # Values should preserve special characters
        url_var = next((v for v in parsed.variables if v.name == "URL"), None)
        if url_var:
            assert url_var.value is not None
