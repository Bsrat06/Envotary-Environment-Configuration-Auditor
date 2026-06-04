# Configuration Reference

EnvSentry uses a `.envsentry.toml` configuration file to define validation rules for environment variables.

## Table of Contents

- [Configuration File Location](#configuration-file-location)
- [Configuration Sections](#configuration-sections)
- [Project Section](#project-section)
- [Files Section](#files-section)
- [Settings Section](#settings-section)
- [Variables Section](#variables-section)
- [Variable Types](#variable-types)
- [Variable Constraints](#variable-constraints)
- [Complete Examples](#complete-examples)

## Configuration File Location

By default, EnvSentry looks for `.envsentry.toml` in:
1. Current directory
2. Project root (directory containing `.git`)

You can specify a custom configuration file:

```bash
envsentry scan --config /path/to/config.toml
```

## Configuration Sections

A complete `.envsentry.toml` file has four main sections:

```toml
[project]          # Project metadata
[files]            # File locations
[settings]         # Validation settings
[variables.*]      # Variable definitions
```

## Project Section

Optional metadata about your project:

```toml
[project]
name = "my-application"
description = "Production API service"
```

**Fields:**
- `name` (optional) - Project name for reports
- `description` (optional) - Project description

## Files Section

Specifies which files to validate:

```toml
[files]
env_file = ".env"
example_file = ".env.example"
```

**Fields:**
- `env_file` (optional, default: `.env`) - Path to environment file
- `example_file` (optional, default: `.env.example`) - Path to example/template file

Paths are relative to the configuration file location.

## Settings Section

Global validation settings:

```toml
[settings]
require_example_file = true
allow_extra_variables = false
```

**Fields:**

### `require_example_file`
- **Type**: boolean
- **Default**: `false`
- **Description**: If `true`, audit fails if example file is missing

### `allow_extra_variables`
- **Type**: boolean
- **Default**: `true`
- **Description**: If `false`, variables in `.env` but not in schema cause errors

## Variables Section

Define validation rules for each variable using `[variables.VARIABLE_NAME]` sections:

```toml
[variables.API_KEY]
type = "string"
required = true
secret = true
min_length = 32
```

## Variable Types

### String Type

```toml
[variables.API_KEY]
type = "string"
required = true
secret = true
min_length = 10
max_length = 100
```

**Constraints:**
- `min_length` - Minimum string length
- `max_length` - Maximum string length
- `choices` - List of allowed values

### Integer Type

```toml
[variables.PORT]
type = "integer"
required = true
min = 1024
max = 65535
```

**Constraints:**
- `min` - Minimum value
- `max` - Maximum value
- `choices` - List of allowed values

### Float Type

```toml
[variables.TIMEOUT]
type = "float"
required = true
min = 0.0
max = 30.0
```

**Constraints:**
- `min` - Minimum value
- `max` - Maximum value

### Boolean Type

```toml
[variables.DEBUG]
type = "boolean"
required = true
```

**Accepted values** (case-insensitive):
- True: `true`, `1`, `yes`, `on`
- False: `false`, `0`, `no`, `off`

### URL Type

```toml
[variables.DATABASE_URL]
type = "url"
required = true
secret = true
```

**Validation:**
- Must have valid URL scheme (http, https, postgresql, mysql, etc.)
- Must have valid URL structure
- Does not verify that URL is reachable (syntax-only validation)

## Variable Constraints

### Common Constraints

#### `required`
- **Type**: boolean
- **Default**: `false`
- **Description**: Variable must exist in `.env` file

```toml
[variables.DATABASE_URL]
required = true
```

#### `secret`
- **Type**: boolean
- **Default**: `false`
- **Description**: Marks variable as secret; value never printed/logged

```toml
[variables.API_KEY]
secret = true
```

### String Constraints

#### `min_length`
- **Type**: integer
- **Description**: Minimum string length

```toml
[variables.PASSWORD]
type = "string"
min_length = 8
```

#### `max_length`
- **Type**: integer
- **Description**: Maximum string length

```toml
[variables.USERNAME]
type = "string"
max_length = 50
```

#### `choices`
- **Type**: array of strings
- **Description**: Value must be one of the listed options

```toml
[variables.ENVIRONMENT]
type = "string"
choices = ["development", "staging", "production"]
```

### Numeric Constraints (integer, float)

#### `min`
- **Type**: number (integer or float)
- **Description**: Minimum value

```toml
[variables.PORT]
type = "integer"
min = 1024
```

#### `max`
- **Type**: number (integer or float)
- **Description**: Maximum value

```toml
[variables.PORT]
type = "integer"
max = 65535
```

#### `choices`
- **Type**: array of numbers
- **Description**: Value must be one of the listed options

```toml
[variables.LOG_LEVEL]
type = "integer"
choices = [0, 1, 2, 3]
```

## Complete Examples

### Minimal Configuration

```toml
[files]
env_file = ".env"

[variables.DATABASE_URL]
type = "url"
required = true
```

### Basic Web Application

```toml
[project]
name = "web-app"

[files]
env_file = ".env"
example_file = ".env.example"

[settings]
require_example_file = true
allow_extra_variables = false

[variables.DATABASE_URL]
type = "url"
required = true
secret = true

[variables.SECRET_KEY]
type = "string"
required = true
secret = true
min_length = 50

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

### Django Application

```toml
[project]
name = "django-app"
description = "Django production application"

[files]
env_file = ".env"
example_file = ".env.example"

[settings]
require_example_file = true
allow_extra_variables = false

[variables.SECRET_KEY]
type = "string"
required = true
secret = true
min_length = 50

[variables.DEBUG]
type = "boolean"
required = true

[variables.ALLOWED_HOSTS]
type = "string"
required = true

[variables.DATABASE_URL]
type = "url"
required = true
secret = true

[variables.REDIS_URL]
type = "url"
required = false
secret = true

[variables.EMAIL_HOST]
type = "string"
required = false

[variables.EMAIL_PORT]
type = "integer"
required = false
min = 1
max = 65535

[variables.EMAIL_USE_TLS]
type = "boolean"
required = false

[variables.STATIC_ROOT]
type = "string"
required = false

[variables.MEDIA_ROOT]
type = "string"
required = false
```

### Node.js/Express Application

```toml
[project]
name = "express-api"

[files]
env_file = ".env"
example_file = ".env.example"

[settings]
require_example_file = true
allow_extra_variables = false

[variables.NODE_ENV]
type = "string"
required = true
choices = ["development", "production", "test"]

[variables.PORT]
type = "integer"
required = true
min = 1024
max = 65535

[variables.DATABASE_URL]
type = "url"
required = true
secret = true

[variables.JWT_SECRET]
type = "string"
required = true
secret = true
min_length = 32

[variables.JWT_EXPIRES_IN]
type = "string"
required = false

[variables.API_BASE_URL]
type = "url"
required = true

[variables.LOG_LEVEL]
type = "string"
required = false
choices = ["debug", "info", "warn", "error"]

[variables.RATE_LIMIT_MAX]
type = "integer"
required = false
min = 1
```

### Microservice with Multiple Backends

```toml
[project]
name = "microservice"

[files]
env_file = ".env"
example_file = ".env.example"

[settings]
require_example_file = true
allow_extra_variables = false

# Database
[variables.DATABASE_URL]
type = "url"
required = true
secret = true

# Redis Cache
[variables.REDIS_URL]
type = "url"
required = true
secret = true

# Message Queue
[variables.RABBITMQ_URL]
type = "url"
required = true
secret = true

# External API
[variables.EXTERNAL_API_KEY]
type = "string"
required = true
secret = true
min_length = 20

[variables.EXTERNAL_API_URL]
type = "url"
required = true

# Monitoring
[variables.SENTRY_DSN]
type = "url"
required = false
secret = true

# Feature Flags
[variables.ENABLE_FEATURE_X]
type = "boolean"
required = false

[variables.ENABLE_FEATURE_Y]
type = "boolean"
required = false
```

## Schema Inference

If no `.envsentry.toml` exists, EnvSentry can infer a basic schema from `.env.example`:

```bash
envsentry init
```

This creates a starter configuration with:
- All variables from `.env.example`
- Type set to `string` for all variables
- `required = true` for all variables
- Variables with names containing "SECRET", "KEY", "TOKEN", "PASSWORD" marked as `secret = true`

You should review and customize the generated configuration to add:
- Proper type definitions
- Numeric constraints (min/max)
- String length constraints
- Allowed choices
- Optional variables

## Best Practices

1. **Mark secrets explicitly** - Use `secret = true` for any sensitive data
2. **Use type validation** - Specify correct types (integer, boolean, url) instead of treating everything as string
3. **Set reasonable constraints** - Add min/max for ports, lengths for secrets
4. **Use choices for enums** - Define allowed values for environment names, log levels, etc.
5. **Require example file** - Set `require_example_file = true` to ensure documentation
6. **Disallow extra variables** - Set `allow_extra_variables = false` to catch typos and unused variables
7. **Document your schema** - Add comments explaining why constraints exist

## Troubleshooting

### Configuration file not found

```
Error: Configuration file not found
```

**Solution**: Create `.envsentry.toml` or use `--config` flag:

```bash
envsentry scan --config /path/to/config.toml
```

### Invalid TOML syntax

```
Error: Failed to parse configuration file
```

**Solution**: Validate TOML syntax. Common issues:
- Missing quotes around string values
- Incorrect section headers (must be `[variables.NAME]`, not `[variables][NAME]`)
- Duplicate sections

### Variable type not recognized

```
Error: Invalid type 'str' for variable 'API_KEY'
```

**Solution**: Use valid types: `string`, `integer`, `float`, `boolean`, `url`

## Additional Resources

- [Validation Rules Reference](rules.md)
- [Usage Examples](examples.md)
- [Security Documentation](security.md)
