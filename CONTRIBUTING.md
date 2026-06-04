# Contributing to Envotary

Thank you for considering contributing to Envotary! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and constructive in all interactions
- Focus on what is best for the project and the community
- Show empathy towards other community members

## Getting Started

### Development Environment Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/yourusername/envotary.git
cd envotary
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in editable mode with development dependencies**

```bash
python -m pip install -e .[dev]
```

This installs Envotary in development mode along with:
- `pytest` - Testing framework
- `ruff` - Linting and formatting
- `mypy` - Type checking
- `build` - Package building

### Project Structure

```
envotary/
├── src/envotary/          # Source code
│   ├── cli.py              # CLI entry point (Typer)
│   ├── parser.py           # .env file parser
│   ├── models.py           # Data models
│   ├── config.py           # Configuration loading (.envotary.toml)
│   ├── discovery.py        # File discovery
│   ├── validators.py       # Validation rules
│   ├── engine.py           # Audit engine
│   ├── exit_codes.py       # Exit code constants
│   └── reporters/          # Output formatters
│       ├── terminal.py     # Rich terminal output
│       └── json.py         # JSON output
├── tests/                  # Test suite
│   ├── test_*.py           # Unit tests
│   ├── test_integration.py # Integration tests
│   ├── test_security.py    # Security tests (critical!)
│   └── fixtures/           # Test fixtures
├── examples/               # Example projects
├── docs/                   # Extended documentation
└── pyproject.toml          # Package configuration
```

## Development Workflow

### 1. Code Style

We use **Ruff** for linting and formatting:

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

### 2. Type Checking

All code must include type hints. Use **mypy** for type checking:

```bash
mypy src/envotary
```

### 3. Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_parser.py -v

# Run with coverage
python -m pytest tests/ --cov=envotary --cov-report=html

# Run only security tests (these must always pass!)
python -m pytest tests/test_security.py -v
```

### 4. Making Changes

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write code following existing patterns
   - Add type hints to all functions
   - Add docstrings to public functions and classes

3. **Write tests**
   - Add unit tests for new functionality
   - Update integration tests if needed
   - Ensure security tests pass if you touched security-sensitive code

4. **Run quality checks**

```bash
# All checks must pass before submitting PR
ruff check src/ tests/
mypy src/envotary
python -m pytest tests/ -v
```

5. **Commit your changes**

```bash
git add .
git commit -m "feat: add your feature description"
```

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

6. **Push and create a pull request**

```bash
git push origin feature/your-feature-name
```

## Security Requirements

**CRITICAL**: Envotary is a security tool. All contributions must maintain security guarantees.

### Security Checklist

Before submitting any PR:

- ✅ Never print, log, or serialize actual secret values
- ✅ All security tests in `tests/test_security.py` must pass
- ✅ No real `.env` files or actual secrets committed
- ✅ Error messages never include secret values
- ✅ No network requests in validation logic
- ✅ No file modifications (read-only operations)
- ✅ No code execution from scanned projects

### Security Test Requirements

If your PR touches any of the following, security tests must be updated:

- Parser logic (secret values must never appear in output)
- Reporter logic (terminal or JSON output)
- Error handling (exceptions must not leak secrets)
- Configuration loading
- Validation engine

### Example: Secure vs Insecure

**❌ Insecure** - Never do this:

```python
# BAD: Prints secret value
if variable.secret and len(value) < min_length:
    print(f"Secret {variable.name} has value '{value}' which is too short")
```

**✅ Secure** - Do this instead:

```python
# GOOD: Never exposes the value
if variable.secret and len(value) < min_length:
    print(f"Secret {variable.name} is too short (minimum: {min_length})")
```

## Pull Request Guidelines

### PR Title

Use Conventional Commits format:

- `feat: add placeholder detection for environment-specific patterns`
- `fix: handle multiline values in .env parser`
- `docs: update configuration examples`

### PR Description

Include:

1. **What**: Brief description of the change
2. **Why**: Rationale for the change
3. **How**: Implementation approach (if non-obvious)
4. **Testing**: What testing was done
5. **Breaking Changes**: Any breaking changes (if applicable)

Example:

```markdown
## What
Adds support for floating-point type validation

## Why
Users requested the ability to validate decimal values like timeouts and rates

## How
- Extended type system to include `float` type
- Added min/max constraints for floats
- Updated validators to handle float parsing

## Testing
- Added unit tests in test_validators.py
- Added integration test with float variables
- All existing tests pass

## Breaking Changes
None
```

## Reporting Issues

### Bug Reports

Include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Minimal steps to reproduce the issue
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**: Python version, OS, Envotary version
6. **Sample Files**: Minimal `.env` and `.envotary.toml` to reproduce (no real secrets!)

### Feature Requests

Include:

1. **Use Case**: Describe the problem you're trying to solve
2. **Proposed Solution**: Your idea for how to solve it
3. **Alternatives**: Alternative solutions you've considered
4. **Additional Context**: Any other relevant information

## Documentation

Documentation updates are always welcome:

- Fix typos or unclear explanations
- Add examples for common use cases
- Improve API documentation
- Add troubleshooting guides

Documentation files:
- `README.md` - Main documentation
- `docs/configuration.md` - Configuration reference
- `docs/rules.md` - Validation rules reference
- `docs/security.md` - Security documentation
- `docs/examples.md` - Usage examples

## Testing Philosophy

- **Unit tests** - Test individual functions and classes in isolation
- **Integration tests** - Test complete workflows (scan command end-to-end)
- **Security tests** - Verify security guarantees (critical!)
- **Edge case tests** - Test boundary conditions and error paths

### Writing Good Tests

```python
def test_feature_description():
    """Test that <specific behavior> when <specific condition>."""
    # Arrange - Set up test data
    variable = Variable(name="API_KEY", type="string", secret=True)
    
    # Act - Execute the code under test
    result = validate_variable(variable, "short")
    
    # Assert - Verify the outcome
    assert result.is_valid is False
    assert result.error_code == "ENV009"
```

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search [existing issues](https://github.com/yourusername/envotary/issues)
3. Open a new issue with the "question" label

## Recognition

Contributors will be recognized in:
- Git commit history
- Release notes
- Project documentation (if significant contribution)

Thank you for contributing to Envotary!
