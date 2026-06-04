# Validation Rules Reference

EnvSentry applies a comprehensive set of validation rules to ensure environment configurations are correct and secure. Each rule has a diagnostic code, severity level, and specific remediation guidance.

## Table of Contents

- [Rule Summary](#rule-summary)
- [Detailed Rules](#detailed-rules)
- [Severity Levels](#severity-levels)
- [Placeholder Detection](#placeholder-detection)

## Rule Summary

| Code   | Severity | Rule Name                    | Description                                    |
|--------|----------|------------------------------|------------------------------------------------|
| ENV001 | error    | Missing Required Variable    | Required variable not defined in `.env`        |
| ENV002 | error    | Type Validation Failed       | Value doesn't match expected type              |
| ENV003 | error    | Unexpected Variable          | Variable in `.env` but not in schema           |
| ENV004 | error    | Duplicate Variable           | Variable defined multiple times                |
| ENV005 | error    | Invalid URL Format           | URL-type variable has invalid syntax           |
| ENV006 | error    | Invalid Choice               | Value not in allowed choices list              |
| ENV007 | error    | Parse Error                  | Malformed `.env` file syntax                   |
| ENV008 | warning  | Placeholder Value Detected   | Variable appears to contain placeholder text   |
| ENV009 | error    | Length Constraint Violation  | String length outside min/max bounds           |
| ENV010 | error    | Numeric Constraint Violation | Numeric value outside min/max bounds           |

## Detailed Rules

### ENV001: Missing Required Variable

**Severity**: Error

**Description**: A variable marked as `required = true` in the schema is not present in the `.env` file.

**When Triggered**:
- Variable defined in `.envsentry.toml` with `required = true`
- Variable not found in `.env` file

**Example**:

`.envsentry.toml`:
```toml
[variables.DATABASE_URL]
type = "url"
required = true
```

`.env`:
```bash
# DATABASE_URL is missing
API_KEY=abc123
```

**Error Output**:
```
ENV001: Missing required variable 'DATABASE_URL'
→ Add DATABASE_URL to your .env file
```

**Remediation**:
1. Add the missing variable to your `.env` file
2. If the variable is not needed, set `required = false` in the schema
3. Check for typos in variable names

**Rationale**: Missing required variables cause runtime failures. This catches configuration issues before deployment.

---

### ENV002: Type Validation Failed

**Severity**: Error

**Description**: The value provided for a variable doesn't match its expected type.

**When Triggered**:
- Variable has a type defined in schema (integer, float, boolean, url)
- Value in `.env` cannot be parsed as that type

**Examples**:

**Integer type mismatch**:
```toml
[variables.PORT]
type = "integer"
```
```bash
PORT=not-a-number  # Error: cannot parse as integer
```

**Boolean type mismatch**:
```toml
[variables.DEBUG]
type = "boolean"
```
```bash
DEBUG=maybe  # Error: not a valid boolean
```

**Error Output**:
```
ENV002: Type validation failed for 'PORT'
Expected type: integer, got: 'not-a-number'
→ Ensure PORT is a valid integer
```

**Remediation**:
1. Provide a value matching the expected type
2. Check type constraints in `.envsentry.toml`
3. For booleans, use: `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off`

**Rationale**: Type mismatches cause runtime errors or unexpected behavior. String "8000" vs integer 8000 can break port binding.

---

### ENV003: Unexpected Variable

**Severity**: Error

**Description**: A variable exists in `.env` but is not defined in the schema, and `allow_extra_variables = false`.

**When Triggered**:
- `.envsentry.toml` has `allow_extra_variables = false` in `[settings]`
- Variable in `.env` has no corresponding `[variables.NAME]` section

**Example**:

`.envsentry.toml`:
```toml
[settings]
allow_extra_variables = false

[variables.API_KEY]
type = "string"
```

`.env`:
```bash
API_KEY=abc123
TYPO_VARIABLE=value  # Not in schema
```

**Error Output**:
```
ENV003: Unexpected variable 'TYPO_VARIABLE'
Variable is not defined in schema
→ Remove TYPO_VARIABLE or add it to .envsentry.toml
```

**Remediation**:
1. Remove the variable from `.env` if it's unused
2. Add the variable to `.envsentry.toml` if it's needed
3. Check for typos in variable names
4. Set `allow_extra_variables = true` if you want to allow undefined variables

**Rationale**: Catches typos and unused variables. Prevents configuration drift.

---

### ENV004: Duplicate Variable

**Severity**: Error

**Description**: The same variable is defined multiple times in the `.env` file.

**When Triggered**:
- Variable name appears more than once in `.env`
- Duplicates may have different values

**Example**:

`.env`:
```bash
PORT=8000
DEBUG=true
PORT=3000  # Duplicate definition
```

**Error Output**:
```
ENV004: Duplicate variable 'PORT' at line 3
Variable already defined at line 1
→ Remove duplicate definition of PORT
```

**Remediation**:
1. Remove duplicate definitions
2. Keep only one definition per variable
3. Check for case variations (PORT vs port) - both are treated as PORT

**Rationale**: Duplicate variables create unpredictable behavior. Different parsers may use the first or last value, causing inconsistency.

---

### ENV005: Invalid URL Format

**Severity**: Error

**Description**: A variable with `type = "url"` has a value that doesn't parse as a valid URL.

**When Triggered**:
- Variable defined with `type = "url"`
- Value doesn't have valid URL structure

**Examples**:

**Missing scheme**:
```bash
DATABASE_URL=localhost:5432/db  # Missing postgresql://
```

**Invalid syntax**:
```bash
API_URL=not a url at all
```

**Valid URLs**:
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/db
API_URL=https://api.example.com/v1
REDIS_URL=redis://localhost:6379/0
```

**Error Output**:
```
ENV005: Invalid URL format for 'DATABASE_URL'
→ Ensure DATABASE_URL is a valid URL with scheme
```

**Remediation**:
1. Add URL scheme (http://, https://, postgresql://, etc.)
2. Check URL syntax for special characters
3. Encode passwords with special characters: `user:p%40ss@host` for `p@ss`

**Rationale**: Invalid URLs cause connection failures. Catching syntax errors early prevents deployment issues.

**Note**: EnvSentry validates URL syntax only. It does not verify that the URL is reachable or that the service exists.

---

### ENV006: Invalid Choice

**Severity**: Error

**Description**: The value is not in the list of allowed choices defined in the schema.

**When Triggered**:
- Variable has `choices` constraint in schema
- Value doesn't match any of the allowed choices

**Example**:

`.envsentry.toml`:
```toml
[variables.ENVIRONMENT]
type = "string"
choices = ["development", "staging", "production"]
```

`.env`:
```bash
ENVIRONMENT=dev  # Not in allowed choices
```

**Error Output**:
```
ENV006: Invalid choice for 'ENVIRONMENT'
Value 'dev' not in allowed choices: development, staging, production
→ Set ENVIRONMENT to one of: development, staging, production
```

**Remediation**:
1. Use one of the allowed values
2. Update `choices` in `.envsentry.toml` if new values are needed
3. Check for typos or case mismatches

**Rationale**: Restricts values to known-good options. Prevents typos in environment names (prod vs production) that could cause logic errors.

---

### ENV007: Parse Error

**Severity**: Error

**Description**: The `.env` file contains malformed syntax that cannot be parsed.

**When Triggered**:
- Unclosed quotes
- Invalid escape sequences
- Malformed lines

**Examples**:

**Unclosed quote**:
```bash
API_KEY="unclosed-string
DEBUG=true
```

**Invalid syntax**:
```bash
=value-without-name
INVALID SPACES=value
```

**Error Output**:
```
ENV007: Parse error in .env at line 1
Unclosed quoted string
→ Fix syntax error in .env file
```

**Remediation**:
1. Fix syntax errors in `.env`
2. Ensure quotes are balanced
3. Check for special characters that need escaping
4. Verify variable names don't contain spaces

**Rationale**: Malformed files won't be parsed correctly by applications, causing silent failures or crashes.

---

### ENV008: Placeholder Value Detected

**Severity**: Warning

**Description**: A variable appears to contain placeholder text that should be replaced with actual values.

**When Triggered**:
- Value matches common placeholder patterns (heuristic detection)
- Common patterns: "your-*-here", "change-me", "replace-this", "example", "placeholder", "todo", "fixme"

**Examples**:

```bash
API_KEY=your-api-key-here
SECRET_KEY=change-me
DATABASE_URL=replace-this-with-actual-url
JWT_SECRET=TODO-add-real-secret
```

**Error Output**:
```
ENV008: Variable 'API_KEY' appears to contain a placeholder value
→ Replace the placeholder in API_KEY with an actual value
```

**Remediation**:
1. Replace placeholder with actual value
2. Generate proper credentials if needed
3. If the value is intentionally this text, this is a false positive (see note below)

**Rationale**: Placeholder values reaching production cause authentication failures and security issues.

**Note**: Placeholder detection is heuristic-based and may produce:
- **False positives**: Legitimate values that match placeholder patterns
- **False negatives**: Placeholders that don't match known patterns

---

### ENV009: Length Constraint Violation

**Severity**: Error

**Description**: A string variable violates `min_length` or `max_length` constraints.

**When Triggered**:
- Variable has `min_length` or `max_length` in schema
- Actual string length is outside the allowed range

**Examples**:

**Too short**:
```toml
[variables.SECRET_KEY]
type = "string"
min_length = 50
```
```bash
SECRET_KEY=short  # Only 5 characters
```

**Too long**:
```toml
[variables.USERNAME]
type = "string"
max_length = 30
```
```bash
USERNAME=this-username-is-way-too-long-for-the-system  # 47 characters
```

**Error Output**:
```
ENV009: Variable 'SECRET_KEY' is too short (minimum length: 50)
Actual length: 5
→ Ensure SECRET_KEY has at least 50 characters
```

**Remediation**:
1. Adjust value to meet length requirements
2. For secrets, generate properly-sized random strings
3. Update constraints in schema if requirements are incorrect

**Rationale**: Short secrets are cryptographically weak. Long values may exceed database column limits or cause truncation.

---

### ENV010: Numeric Constraint Violation

**Severity**: Error

**Description**: A numeric variable (integer or float) violates `min` or `max` constraints.

**When Triggered**:
- Variable has `min` or `max` in schema
- Actual numeric value is outside the allowed range

**Examples**:

**Below minimum**:
```toml
[variables.PORT]
type = "integer"
min = 1024
```
```bash
PORT=80  # Below minimum
```

**Above maximum**:
```toml
[variables.TIMEOUT]
type = "float"
max = 30.0
```
```bash
TIMEOUT=60.0  # Above maximum
```

**Error Output**:
```
ENV010: Variable 'PORT' value 80 is below minimum (1024)
→ Set PORT to a value >= 1024
```

**Remediation**:
1. Adjust value to be within allowed range
2. Update constraints in schema if requirements changed
3. Check for unit mismatches (seconds vs milliseconds)

**Rationale**: Out-of-range values cause failures. Port 80 requires root privileges. Timeouts too large cause poor UX.

---

## Severity Levels

### Error
- Validation failure that should block deployment
- Exit code 1
- Must be fixed before production

### Warning
- Potential issue that should be reviewed
- Exit code 1 (configurable to be treated as error)
- May be acceptable in some contexts (e.g., legitimate value matching placeholder pattern)

### Info
- Informational message
- Exit code 0
- No action required

## Placeholder Detection

EnvSentry uses heuristic pattern matching to detect placeholder values.

### Detected Patterns

The following patterns trigger ENV008 warnings:

1. **Generic placeholders**:
   - `your-*-here` (e.g., `your-api-key-here`)
   - `change-me`, `changeme`
   - `replace-this`, `replace-me`
   - `example`, `example-*`
   - `placeholder`
   - `<placeholder>`, `[placeholder]`

2. **Development markers**:
   - `todo`, `fixme`
   - `xxx`, `yyy`, `zzz`

3. **Generic test values**:
   - `test`, `testing`
   - `dummy`
   - `sample`

4. **Quotes/brackets**:
   - Values in angle brackets: `<value>`
   - Values in square brackets: `[value]`

### Legitimate Values That May Trigger False Positives

- Service names: `example-service`
- API paths: `https://api.example.com`
- Email domains: `user@example.com`
- Usernames: `test_user`

### Pattern Matching Rules

- Case-insensitive
- Matches if pattern appears anywhere in value
- Whole-word matching for some patterns
- Special weighting for variables marked `secret = true`

### Handling False Positives

If a legitimate value triggers ENV008:

1. **Option 1**: Accept the warning (it won't block the scan)
2. **Option 2**: Modify the value slightly if possible
3. **Option 3**: Document that this is expected

False positives are intentional - it's better to warn about a legitimate value than to miss a real placeholder.

### Limitations

- **Cannot detect all placeholders**: Custom or unusual placeholder patterns may not be caught
- **Context-unaware**: Cannot determine if "test" is a placeholder or a legitimate test environment name
- **No semantic understanding**: Cannot tell if a value is functionally valid for its purpose

## Best Practices

1. **Fix errors before warnings**: Address all errors first, then review warnings
2. **Review warnings carefully**: Warnings indicate potential issues but may be false positives
3. **Don't disable warnings**: Even false positives are valuable reminders to review configuration
4. **Use strict validation in CI**: Set `allow_extra_variables = false` to catch all issues
5. **Document exceptions**: If a warning is a known false positive, document why
6. **Regular audits**: Run EnvSentry regularly to catch configuration drift

## Additional Resources

- [Configuration Reference](configuration.md)
- [Security Documentation](security.md)
- [Usage Examples](examples.md)
