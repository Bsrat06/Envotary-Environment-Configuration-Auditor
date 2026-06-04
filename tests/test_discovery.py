"""Tests for discovery module."""


from envotary.discovery import discover_files


def test_discover_all_files(tmp_path):
    """Test discovery when all files exist."""
    # Create files
    (tmp_path / ".env").touch()
    (tmp_path / ".env.example").touch()
    (tmp_path / ".envotary.toml").touch()

    result = discover_files(tmp_path)

    assert result["env_file"] == tmp_path / ".env"
    assert result["example_file"] == tmp_path / ".env.example"
    assert result["config_file"] == tmp_path / ".envotary.toml"


def test_discover_no_files(tmp_path):
    """Test discovery when no files exist."""
    result = discover_files(tmp_path)

    assert result["env_file"] is None
    assert result["example_file"] is None
    assert result["config_file"] is None


def test_discover_partial_files(tmp_path):
    """Test discovery when only some files exist."""
    (tmp_path / ".env").touch()
    (tmp_path / ".envotary.toml").touch()

    result = discover_files(tmp_path)

    assert result["env_file"] == tmp_path / ".env"
    assert result["example_file"] is None
    assert result["config_file"] == tmp_path / ".envotary.toml"


def test_explicit_env_file(tmp_path):
    """Test discovery with explicit env file path."""
    custom_env = tmp_path / "custom.env"
    custom_env.touch()

    result = discover_files(tmp_path, env_file="custom.env")

    assert result["env_file"] == custom_env
    assert result["example_file"] is None
    assert result["config_file"] is None


def test_explicit_example_file(tmp_path):
    """Test discovery with explicit example file path."""
    custom_example = tmp_path / "my.env.example"
    custom_example.touch()

    result = discover_files(tmp_path, example_file="my.env.example")

    assert result["env_file"] is None
    assert result["example_file"] == custom_example
    assert result["config_file"] is None


def test_explicit_paths_absolute(tmp_path):
    """Test discovery with absolute paths."""
    custom_env = tmp_path / "custom.env"
    custom_env.touch()

    result = discover_files(tmp_path, env_file=str(custom_env))

    assert result["env_file"] == custom_env


def test_explicit_nonexistent_file(tmp_path):
    """Test discovery with explicit path to nonexistent file."""
    result = discover_files(tmp_path, env_file="nonexistent.env")

    assert result["env_file"] is None


def test_subdirectory_files(tmp_path):
    """Test discovery with files in subdirectories."""
    subdir = tmp_path / "config"
    subdir.mkdir()
    (subdir / ".env").touch()

    result = discover_files(tmp_path, env_file="config/.env")

    assert result["env_file"] == subdir / ".env"
