# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-04

### Added

#### Core Functionality
- Environment configuration auditing CLI tool for detecting configuration problems before deployment
- Support for `.env`, `.env.example`, and `.envsentry.toml` configuration files
- Automatic schema discovery from `.env.example` files
- Explicit schema definition via `.envsentry.toml` TOML configuration

#### Validation Rules
- **ENV001**: Missing required variables detection
- **ENV002**: Undocumented variables detection
- **ENV003**: Duplicate variable declarations detection
- **ENV004**: Empty required values detection
- **ENV005**: Invalid type validation (string, integer, float, boolean, URL)
- **ENV006**: Invalid URL syntax validation (no network requests)
- **ENV007**: Invalid choice validation (enum-like constraints)
- **ENV008**: Placeholder value detection (e.g., "your-secret-here", "replace-me")
- **ENV009**: Length constraint validation (min_length, max_length)
- **ENV010**: Numeric constraint validation (min, max for integers and floats)

#### CLI Commands
- `envsentry scan` - Scan project directory for environment configuration issues
  - `--path` option to specify target project directory
  - `--env-file` option to specify custom environment file path
  - `--format` option for output format (terminal or json)
- `envsentry init` - Generate starter `.envsentry.toml` configuration file

#### Reporters
- **Terminal Reporter**: Professional Rich-based output with:
  - Findings grouped by severity (error, warning, info)
  - Diagnostic codes, variable names, file:line references
  - Remediation guidance for each finding
  - Clean pass/fail status display
- **JSON Reporter**: Machine-readable structured output with:
  - Tool version and timestamp
  - Project metadata
  - Summary statistics
  - Complete findings with all metadata
  - Stable, deterministic output (sorted keys)

#### Exit Codes
- `0` - No error-level findings (audit passed)
- `1` - Error-level findings detected (audit failed)
- `2` - Invalid invocation or execution failure

#### Parser Features
- Full dotenv syntax support:
  - Basic `KEY=value` declarations
  - Single and double-quoted values
  - Comments (lines starting with `#`)
  - Whitespace handling
  - Values containing equals signs
  - Empty values
  - Duplicate key detection
  - Line number tracking for accurate error reporting

#### Type Validation
- **String**: With min_length, max_length constraints
- **Integer**: With min, max constraints, rejects floats
- **Float**: With min, max constraints, accepts integers
- **Boolean**: Supports true/false, yes/no, on/off, 1/0 (case-insensitive)
- **URL**: Syntax validation for http/https/postgresql/mysql/redis URLs

#### Schema Constraints
- `required` - Mark variables as mandatory
- `secret` - Flag sensitive variables (for documentation, no special handling)
- `type` - Specify expected data type
- `choices` - Restrict to allowed values
- `min_length` / `max_length` - String length constraints
- `min` / `max` - Numeric boundary constraints

#### Documentation
- Comprehensive README with quick start guide and examples
- Configuration reference (`docs/configuration.md`)
- Complete validation rules documentation (`docs/rules.md`)
- Security guarantees and threat model (`docs/security.md`)
- Usage examples and CI integration guide (`docs/examples.md`)
- Contributing guidelines (`CONTRIBUTING.md`)
- MIT License

#### Examples
- **Basic**: Minimal application example with clean audit
- **Django**: Django project example demonstrating length constraint violation
- **Node.js**: Express application example demonstrating placeholder detection

#### Testing
- 171 comprehensive tests covering:
  - Parser functionality (19 tests)
  - Configuration loading (10 tests)
  - File discovery (8 tests)
  - Validators (38 tests)
  - Audit engine (9 tests)
  - Integration scenarios (13 tests)
  - CLI commands (16 tests)
  - Reporters (11 tests)
  - Edge cases (21 tests)
  - Data models (21 tests)
  - Security validation (9 tests)
- Critical secret leakage prevention tests
- Edge case coverage (malformed files, missing files, large files, path handling)

#### CI/CD
- GitHub Actions workflow with:
  - Linting with Ruff
  - Type checking with mypy
  - Test suite execution on Python 3.11 and 3.12
  - Security test validation
  - Package build verification

#### Security Guarantees
- Never exposes actual environment variable values in any output
- Never modifies scanned files during audit
- Never executes code from scanned projects
- Never makes network requests during validation
- Safe symlink handling (no traversal outside project root)
- No credentials storage or transmission

### Technical Details
- Python 3.11+ support (tested on 3.11 and 3.12)
- Modern `src/` package layout
- Type hints throughout codebase
- Zero runtime network dependencies
- Lightweight dependency footprint (Typer, Rich, stdlib)

---

## [Unreleased]

No unreleased changes.

---

## Release Notes

### v1.0.0 - Initial Release

EnvSentry v1.0.0 is the first stable release of this security-focused environment configuration auditing tool. It provides production-ready functionality for detecting configuration problems in `.env` files before they cause runtime failures.

**Key Features:**
- 10+ validation rules with stable diagnostic codes
- Terminal and JSON output formats
- Automatic schema discovery
- Comprehensive test coverage (171 tests)
- Full documentation and examples
- CI-ready with proper exit codes

**Security Focus:**
EnvSentry is designed with security as a core principle. It never exposes actual environment variable values in any output, making it safe to use in CI/CD pipelines and team environments.

**Use Cases:**
- Pre-deployment configuration validation
- CI/CD pipeline integration
- Local development environment checks
- Pre-commit hooks
- Multi-environment configuration auditing

**Getting Started:**
```bash
pip install envsentry
cd your-project
envsentry scan
```

**Limitations:**
- URL validation is syntax-only (no network reachability checks)
- Boolean parsing uses documented heuristics, may not match all interpreters
- Placeholder detection uses pattern matching, cannot guarantee secret security
- Python projects have first-class support; other languages supported via generic rules

---

[1.0.0]: https://github.com/yourusername/envsentry/releases/tag/v1.0.0
