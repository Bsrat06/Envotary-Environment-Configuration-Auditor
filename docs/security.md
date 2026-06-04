# Security Documentation

Envotary is designed with security as the top priority. This document details the security guarantees, threat model, and verification methods.

## Table of Contents

- [Security Guarantees](#security-guarantees)
- [Threat Model](#threat-model)
- [Security Features](#security-features)
- [Verification](#verification)
- [Security Best Practices](#security-best-practices)
- [Reporting Security Issues](#reporting-security-issues)

## Security Guarantees

Envotary provides the following security guarantees:

### 1. Never Prints Secret Values

**Guarantee**: Secret variable values are never written to terminal output.

Variables marked with `secret = true` have their values redacted in all output formats:
- Terminal output shows `[REDACTED]` instead of actual values
- Error messages reference variable names but never include values
- Validation feedback describes issues without exposing values

**Example**:
```bash
# .env
API_KEY=super-secret-key-abc123

# Output - value is never shown
✗ ENV009: Variable 'API_KEY' is too short (minimum length: 32)
  → Ensure API_KEY has at least 32 characters
```

### 2. Never Serializes Secret Values

**Guarantee**: Secret values are never included in JSON output or any serialized format.

When using `--format json`, secret variables appear with `"value": "[REDACTED]"`:

```json
{
  "variable": "API_KEY",
  "type": "string",
  "value": "[REDACTED]"
}
```

### 3. No Network Requests

**Guarantee**: Envotary never makes network connections.

All validation is performed locally:
- No telemetry or analytics
- No version checks over network
- No data transmission to external services
- URL validation is syntax-only (does not test reachability)

### 4. No File Modifications

**Guarantee**: Envotary is read-only and never modifies scanned files.

- Only reads `.env`, `.env.example`, and `.envotary.toml`
- Never writes to configuration or environment files
- Never creates backup files
- Never modifies file permissions or timestamps

### 5. No Code Execution

**Guarantee**: Envotary never executes code from scanned projects.

- Does not run shell commands
- Does not evaluate expressions in `.env` files
- Does not import or execute Python modules from scanned projects
- Purely static analysis

### 6. No Shell Commands

**Guarantee**: Envotary never invokes shell commands or subprocesses.

- No calls to `subprocess`, `os.system`, `exec`, or similar
- No shell expansion or variable interpolation
- No command injection vulnerabilities

### 7. Careful Symlink Handling

**Guarantee**: Symlinks are resolved safely without escaping project boundaries.

- Symlinks in project paths are resolved
- Does not follow symlinks outside project root
- Prevents directory traversal attacks

### 8. No Writing to Config Files

**Guarantee**: Configuration files are never modified.

- `.envotary.toml` is read-only
- `envotary init` creates new file but never overwrites existing
- No automatic schema updates or migrations

### 9. No Secrets in Exceptions

**Guarantee**: Exception messages and stack traces never include secret values.

Even in error conditions:
- Variable names may appear in errors
- File paths may appear in errors
- Secret values never appear in exception messages or stack traces

**Example**:
```python
# Even if validation crashes, secret values are not leaked
try:
    validate_secret_variable(api_key)
except Exception as e:
    # e.message contains only "Validation failed for API_KEY"
    # Never contains the actual secret value
```

### 10. No Raw Parser Input in Errors

**Guarantee**: Error messages sanitize input and never echo raw secret values.

Parser errors reference line numbers and variable names:
```
ENV007: Parse error at line 5
Unclosed quoted string in variable 'DATABASE_URL'
```

Not:
```
ENV007: Parse error: could not parse "postgresql://user:secret_password@..."
```

### 11. Safe File Permission Handling

**Guarantee**: File permissions are checked but never modified.

- Warns about world-readable `.env` files (security risk)
- Never changes file permissions automatically
- User decides remediation

### 12. Limitations of Heuristic Detection Clearly Documented

**Guarantee**: Placeholder detection limitations are explicitly documented.

- Heuristic-based placeholder detection may have false positives/negatives
- Documentation clearly states what can and cannot be detected
- Users understand tool limitations

## Threat Model

### What Envotary Protects Against

Envotary is designed to catch configuration errors during development and in CI pipelines:

✅ **Missing required variables** - Catches before deployment  
✅ **Type mismatches** - Prevents runtime type errors  
✅ **Placeholder values** - Warns about unreplaced placeholders  
✅ **Duplicate definitions** - Catches conflicting configurations  
✅ **Constraint violations** - Enforces length, range, and choice constraints  
✅ **Configuration drift** - Detects variables not in schema  

### What Envotary Does NOT Protect Against

❌ **Secret exposure in git history** - Use git-secrets, truffleHog, or similar tools  
❌ **Secret exposure in logs** - Application must sanitize logs  
❌ **Weak secrets** - Does not assess cryptographic strength beyond length  
❌ **Leaked secrets in public repositories** - Use GitHub secret scanning  
❌ **Runtime security issues** - Not a runtime security monitor  
❌ **Network-based attacks** - No runtime protection  
❌ **Secret rotation** - Not a secret management system  

### Intended Use Cases

Envotary is intended for:

- Local development environment validation
- Pre-commit hooks in development
- CI/CD pipeline configuration checks
- Developer workstation security audits
- Configuration review before deployment

### NOT Intended For

Envotary is NOT intended for:

- Production secret scanning (use vault solutions like HashiCorp Vault)
- Continuous security monitoring (use SIEM tools)
- Detecting already-leaked secrets (use secret scanning services)
- Secret storage (use proper secret management)
- Compliance auditing (use compliance-specific tools)

## Security Features

### Secret Redaction

All secret values are redacted using a consistent pattern:

```python
def redact_secret(value: str) -> str:
    """Redact secret value for display."""
    return "[REDACTED]"
```

Redaction is applied:
- In terminal output
- In JSON output
- In error messages
- In debug logs (if any)
- In exception messages

### Type Safety

Envotary uses Python type hints throughout:

```python
from dataclasses import dataclass

@dataclass
class Variable:
    name: str
    type: VariableType
    required: bool
    secret: bool
```

Type checking with `mypy` ensures:
- No accidental value exposure in wrong contexts
- Type-safe value handling
- Compile-time verification of security properties

### Input Validation

All external input is validated:

- `.env` files are parsed with error handling
- `.envotary.toml` is validated against schema
- File paths are sanitized and validated
- User input is validated before processing

### Secure Defaults

Security-conscious defaults:

- Secrets are not printed by default (must explicitly opt-in to redacted display)
- Files outside project are not scanned
- Symlinks are not followed outside project boundaries
- No network access by default (and no option to enable it)

## Verification

### How to Verify Security Guarantees

Envotary includes comprehensive security tests in `tests/test_security.py`.

#### Run Security Tests

```bash
cd /path/to/envotary
python -m pytest tests/test_security.py -v
```

#### Security Test Coverage

The security test suite verifies:

1. **No secret exposure in terminal output**
   - Tests that secret values never appear in terminal reports
   - Validates redaction for various output scenarios

2. **No secret exposure in JSON output**
   - Tests that JSON serialization redacts secrets
   - Validates all JSON output paths

3. **No secret exposure in error messages**
   - Tests exception handling with secret variables
   - Validates error messages never include values

4. **No network requests**
   - Mocks network calls to ensure none are made
   - Tests URL validation doesn't make requests

5. **No file modifications**
   - Monitors filesystem for writes during scan
   - Validates read-only behavior

6. **No code execution**
   - Tests that variable values aren't evaluated
   - Validates no subprocess calls

### Manual Verification

You can manually verify security guarantees:

#### 1. Test Secret Redaction

Create a test `.env` with a secret:

```bash
# test/.env
SECRET_API_KEY=my-actual-secret-value
```

Configure as secret:

```toml
# test/.envotary.toml
[variables.SECRET_API_KEY]
type = "string"
required = true
secret = true
```

Run scan and verify output never contains `my-actual-secret-value`:

```bash
envotary scan --path test/
envotary scan --path test/ --format json
```

#### 2. Test Network Isolation

Monitor network with Wireshark or similar while running:

```bash
envotary scan
```

Verify no network packets are sent.

#### 3. Test Read-Only Behavior

Make files read-only and verify scan still works:

```bash
chmod 444 .env .envotary.toml
envotary scan
```

Monitor filesystem with `strace` (Linux) or Process Monitor (Windows) to verify no write operations.

## Security Best Practices

### For Users

1. **Mark secrets explicitly**
   ```toml
   [variables.DATABASE_PASSWORD]
   secret = true
   ```

2. **Never commit real `.env` files**
   ```bash
   # .gitignore
   .env
   .env.local
   .env.*.local
   ```

3. **Use `.env.example` for documentation**
   ```bash
   # .env.example - safe to commit
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   ```

4. **Run Envotary in CI**
   ```yaml
   - name: Audit environment configuration
     run: envotary scan --strict
   ```

5. **Review warnings carefully**
   - Warnings about placeholders should be investigated
   - False positives should be documented

6. **Use proper secret management in production**
   - Envotary validates config structure
   - Use Vault, AWS Secrets Manager, etc. for runtime secrets

### For Contributors

1. **Never log or print values in new code**
2. **Always redact secrets in output**
3. **Add security tests for new features**
4. **Use type hints to prevent accidents**
5. **Review PRs for security implications**
6. **Run security test suite before submitting**

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines.

## Reporting Security Issues

### If You Find a Security Vulnerability

**Do NOT open a public GitHub issue.**

Instead:

1. Email security concerns to: [security contact email - update this]
2. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

3. We will respond within 48 hours
4. We will work with you to verify and fix the issue
5. We will coordinate disclosure after fix is released

### Security Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

- (No vulnerabilities reported yet)

## Security Audit History

| Date       | Auditor | Scope                          | Findings |
|------------|---------|--------------------------------|----------|
| 2024-11-14 | Self    | Initial security test suite    | 0        |

## Compliance

Envotary is designed to support security compliance but is not a compliance tool:

- **PCI DSS**: Helps prevent credential exposure (not sufficient alone)
- **SOC 2**: Demonstrates configuration validation (not sufficient alone)
- **HIPAA**: Helps secure configuration (not sufficient alone)

Consult compliance experts for your specific requirements.

## Additional Resources

- [Configuration Reference](configuration.md)
- [Validation Rules](rules.md)
- [Usage Examples](examples.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

---

**Last Updated**: 2024-11-14  
**Version**: 1.0.0
