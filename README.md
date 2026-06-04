# Envotary

**Environment Configuration Auditor**

Envotary is a security-focused CLI tool that audits environment variable configurations in your projects. It validates `.env` files against schemas, detects common configuration errors, and ensures secrets are properly configured—without ever exposing actual secret values.

## Why Audit Environment Configurations?

Environment variables are a common attack vector and source of bugs:

- **Missing required variables** cause runtime crashes in production
- **Type mismatches** lead to silent failures or security vulnerabilities
- **Placeholder values** like `your-api-key-here` accidentally reach production
- **Duplicate definitions** create unpredictable behavior
- **Exposed secrets** in logs and error messages compromise security

Envotary catches these issues during development and in CI pipelines, before they reach production.

## Key Features

- ✅ **Missing Variable Detection** - Ensures all required environment variables are defined
- ✅ **Type Validation** - Validates variables as strings, integers, floats, booleans, or URLs
- ✅ **Duplicate Detection** - Catches duplicate variable definitions that cause conflicts
- ✅ **Placeholder Detection** - Warns about common placeholder patterns that shouldn't reach production
- ✅ **No Secret Exposure** - Never prints, logs, or serializes actual secret values (security-first design)
- ✅ **Schema Definition** - Define validation rules in `.envotary.toml` with type constraints
- ✅ **Multiple Output Formats** - Human-readable terminal output or JSON for CI/tooling integration
- ✅ **CI Integration Ready** - Exit codes designed for automated pipelines

## Installation

### From PyPI (when published)

```bash
pip install envotary
```

### Local Installation (Development)

```bash
git clone https://github.com/yourusername/envotary.git
cd envotary
python -m pip install -e .
```

## Quick Start

### 1. Create an `.env.example` template

```bash
# .env.example
API_KEY=your-api-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DEBUG=true
PORT=8000
ENVIRONMENT=development
```

### 2. Create your actual `.env` file

```bash
# .env
API_KEY=fake-api-key-abc123def456
DATABASE_URL=postgresql://dbuser:securepass123@localhost:5432/myapp
DEBUG=true
PORT=8000
ENVIRONMENT=development
```

### 3. Create `.envotary.toml` configuration

```toml
[project]
name = "my-project"

[files]
env_file = ".env"
example_file = ".env.example"

[settings]
require_example_file = true
allow_extra_variables = false

[variables.API_KEY]
type = "string"
required = true
secret = true
min_length = 10

[variables.DATABASE_URL]
type = "url"
required = true
secret = true

[variables.DEBUG]
type = "boolean"
required = true

[variables.PORT]
type = "integer"
required = true
min = 1024
max = 65535

[variables.ENVIRONMENT]
type = "string"
required = true
choices = ["development", "staging", "production"]
```

### 4. Run Envotary

```bash
envotary scan
```

## Example Output

### Successful Audit

```
╭───────────────────────────────────────────────────────────────────────────────╮
│ Envotary Security Audit                                                      │
│ Project: /path/to/your/project                                                │
╰───────────────────────────────────────────────────────────────────────────────╯

Summary: 0 error(s) | 0 warning(s)

✓ No issues found

╭───────────────────────────────────────────────────────────────────────────────╮
│ ✓ Audit passed                                                                │
╰───────────────────────────────────────────────────────────────────────────────╯
```

### Failed Audit

```
╭───────────────────────────────────────────────────────────────────────────────╮
│ Envotary Security Audit                                                      │
│ Project: /path/to/your/project                                                │
╰───────────────────────────────────────────────────────────────────────────────╯

Summary: 1 error(s) | 1 warning(s)

Errors:
 Code    Variable    Location         Issue                                           
 ENV009  JWT_SECRET  .env:5           Variable 'JWT_SECRET' is too short (min: 32)    
                                      → Ensure JWT_SECRET has at least 32 characters  

Warnings:
 Code    Variable    Location         Issue                                           
 ENV008  JWT_SECRET  .env:5           Variable appears to contain a placeholder value 
                                      → Replace the placeholder with an actual value  

╭───────────────────────────────────────────────────────────────────────────────╮
│ ✗ Audit failed with 1 error(s)                                               │
╰───────────────────────────────────────────────────────────────────────────────╯
```

## JSON Output

For CI/CD integration or tooling, use JSON format:

```bash
envotary scan --format json
```

Example output:

```json
{
  "tool_version": "1.0.0",
  "scan_timestamp": "2024-11-14T14:53:20.680435+00:00",
  "project_path": "/path/to/your/project",
  "summary": {
    "total_findings": 0,
    "by_severity": {
      "error": 0,
      "warning": 0,
      "info": 0
    }
  },
  "findings": []
}
```

## Validation Rules

| Code   | Severity | Description                                         |
|--------|----------|-----------------------------------------------------|
| ENV001 | error    | Missing required variable                           |
| ENV002 | error    | Type validation failed (wrong type)                 |
| ENV003 | error    | Variable defined in `.env` but not in schema        |
| ENV004 | error    | Duplicate variable definition                       |
| ENV005 | error    | Invalid URL format                                  |
| ENV006 | error    | Value not in allowed choices                        |
| ENV007 | error    | Parse error (malformed `.env` syntax)               |
| ENV008 | warning  | Placeholder value detected                          |
| ENV009 | error    | Length constraint violation (min_length, max_length)|
| ENV010 | error    | Numeric constraint violation (min, max)             |

## Exit Codes

- **0** - Audit passed (no errors or warnings)
- **1** - Audit failed (validation errors found)
- **2** - Execution error (invalid config, file not found, etc.)

## Security Guarantees

Envotary is designed with security as the top priority:

1. **Never exposes secret values** - Secret variable values are never printed to terminal, written to logs, or included in JSON output
2. **No network requests** - All validation is local; no data leaves your machine
3. **No file modifications** - Envotary only reads files, never writes or modifies them
4. **No code execution** - Does not execute any code from scanned projects
5. **Safe error handling** - Error messages never include actual secret values
6. **Symlink safety** - Follows symlinks safely without escaping project boundaries

See [docs/security.md](docs/security.md) for detailed security documentation.

## Supported Dotenv Syntax

Envotary supports standard `.env` file syntax:

```bash
# Comments
VARIABLE=value
QUOTED="value with spaces"
SINGLE_QUOTED='value with spaces'
EMPTY_VALUE=
EXPORT export VARIABLE=value
MULTILINE="line1
line2"
```

## Limitations

- **Placeholder detection is heuristic-based** - May not catch all placeholder patterns or may flag legitimate values
- **URL validation is syntax-only** - Does not verify that URLs are reachable or valid
- **No runtime validation** - Envotary validates configuration files, not runtime behavior
- **Boolean values** - Accepts `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off` (case-insensitive)

## Configuration

See [docs/configuration.md](docs/configuration.md) for complete `.envotary.toml` configuration reference.

## Examples

The `examples/` directory contains realistic sample projects:

- **[examples/basic](examples/basic/)** - Minimal example with core features
- **[examples/django](examples/django/)** - Django project configuration
- **[examples/node](examples/node/)** - Node.js/Express project configuration

See [docs/examples.md](docs/examples.md) for detailed usage examples.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/envotary.git
cd envotary

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
python -m pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run security tests specifically
python -m pytest tests/test_security.py -v

# Run with coverage
python -m pytest tests/ --cov=envotary --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/envotary

# Format code
ruff format src/ tests/
```

### Building

```bash
# Install build tool
python -m pip install build

# Build package
python -m build

# Install from built package
pip install dist/envotary-*.whl
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Security Note**: Never commit real `.env` files or actual secrets to the repository. All example files must use clearly fake, non-functional credentials.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Documentation

- [Configuration Reference](docs/configuration.md)
- [Validation Rules](docs/rules.md)
- [Security Documentation](docs/security.md)
- [Usage Examples](docs/examples.md)
