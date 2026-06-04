# Usage Examples

This document provides practical examples of using EnvSentry in different scenarios.

## Table of Contents

- [Example 1: Basic Project Setup](#example-1-basic-project-setup)
- [Example 2: Django Project](#example-2-django-project)
- [Example 3: Node.js Project](#example-3-nodejs-project)
- [Example 4: CI Integration (GitHub Actions)](#example-4-ci-integration-github-actions)
- [Example 5: Strict Mode for Pre-commit Hooks](#example-5-strict-mode-for-pre-commit-hooks)
- [Example 6: JSON Output for Tooling Integration](#example-6-json-output-for-tooling-integration)

## Example 1: Basic Project Setup

### Scenario

You have a basic web application with a few environment variables. You want to validate that all required variables are present and have correct types.

### Project Structure

```
myapp/
├── .env
├── .env.example
└── .envsentry.toml
```

### Files

**`.env.example`** (template - safe to commit):
```bash
# API Configuration
API_KEY=your-api-key-here
API_BASE_URL=https://api.example.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Application Settings
DEBUG=true
PORT=8000
ENVIRONMENT=development
```

**`.env`** (actual config - DO NOT COMMIT):
```bash
# API Configuration
API_KEY=fake-api-key-abc123def456
API_BASE_URL=https://api.example.com

# Database
DATABASE_URL=postgresql://myuser:mypass123@localhost:5432/myapp

# Application Settings
DEBUG=true
PORT=8000
ENVIRONMENT=development
```

**`.envsentry.toml`**:
```toml
[project]
name = "myapp"
description = "Basic web application"

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
min_length = 20

[variables.API_BASE_URL]
type = "url"
required = true

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

### Running EnvSentry

```bash
cd myapp
envsentry scan
```

### Expected Output

```
╭───────────────────────────────────────────────────────────────╮
│ EnvSentry Security Audit                                      │
│ Project: myapp                                                │
╰───────────────────────────────────────────────────────────────╯

Summary: 0 error(s) | 0 warning(s)

✓ No issues found

╭───────────────────────────────────────────────────────────────╮
│ ✓ Audit passed                                                │
╰───────────────────────────────────────────────────────────────╯
```

## Example 2: Django Project

### Scenario

Django project with typical Django environment variables including SECRET_KEY, database, static files, and email configuration.

### `.envsentry.toml`

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

# Core Django Settings
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

# Database
[variables.DATABASE_URL]
type = "url"
required = true
secret = true

# Cache
[variables.REDIS_URL]
type = "url"
required = false
secret = true

# Email Configuration
[variables.EMAIL_HOST]
type = "string"
required = false

[variables.EMAIL_PORT]
type = "integer"
required = false
min = 1
max = 65535

[variables.EMAIL_HOST_USER]
type = "string"
required = false

[variables.EMAIL_HOST_PASSWORD]
type = "string"
required = false
secret = true

[variables.EMAIL_USE_TLS]
type = "boolean"
required = false

# Static and Media Files
[variables.STATIC_ROOT]
type = "string"
required = false

[variables.MEDIA_ROOT]
type = "string"
required = false

[variables.AWS_STORAGE_BUCKET_NAME]
type = "string"
required = false

# Application Settings
[variables.ENVIRONMENT]
type = "string"
required = true
choices = ["development", "staging", "production"]
```

### `.env.example`

```bash
# Django Core Settings
SECRET_KEY=your-secret-key-here-minimum-50-characters-for-security-compliance
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1,.example.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Cache
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=user@example.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=true

# Static and Media Files
STATIC_ROOT=/var/www/static
MEDIA_ROOT=/var/www/media
AWS_STORAGE_BUCKET_NAME=my-bucket

# Application
ENVIRONMENT=production
```

### Running EnvSentry

```bash
envsentry scan --path /path/to/django-app
```

See the [examples/django](../examples/django/) directory for a complete working example.

## Example 3: Node.js Project

### Scenario

Express.js API with JWT authentication, database, and external API integration.

### `.envsentry.toml`

```toml
[project]
name = "express-api"
description = "Node.js Express API"

[files]
env_file = ".env"
example_file = ".env.example"

[settings]
require_example_file = true
allow_extra_variables = false

# Node Environment
[variables.NODE_ENV]
type = "string"
required = true
choices = ["development", "production", "test"]

[variables.PORT]
type = "integer"
required = true
min = 1024
max = 65535

# Database
[variables.DATABASE_URL]
type = "url"
required = true
secret = true

# JWT Configuration
[variables.JWT_SECRET]
type = "string"
required = true
secret = true
min_length = 32

[variables.JWT_EXPIRES_IN]
type = "string"
required = false

# External API
[variables.API_BASE_URL]
type = "url"
required = true

[variables.API_KEY]
type = "string"
required = true
secret = true
min_length = 20

# Logging
[variables.LOG_LEVEL]
type = "string"
required = false
choices = ["debug", "info", "warn", "error"]

# Rate Limiting
[variables.RATE_LIMIT_MAX]
type = "integer"
required = false
min = 1
max = 10000

[variables.RATE_LIMIT_WINDOW_MS]
type = "integer"
required = false
min = 1000
```

### `.env.example`

```bash
# Node Configuration
NODE_ENV=development
PORT=3000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT Authentication
JWT_SECRET=your-jwt-secret-here-minimum-32-characters
JWT_EXPIRES_IN=24h

# External API
API_BASE_URL=https://api.example.com/v1
API_KEY=your-api-key-here

# Logging
LOG_LEVEL=info

# Rate Limiting
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW_MS=900000
```

See the [examples/node](../examples/node/) directory for a complete working example.

## Example 4: CI Integration (GitHub Actions)

### Scenario

Run EnvSentry as part of your CI pipeline to catch configuration issues before deployment.

### GitHub Actions Workflow

**`.github/workflows/ci.yml`**:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  env-audit:
    name: Environment Configuration Audit
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install EnvSentry
        run: pip install envsentry
      
      - name: Run EnvSentry audit
        run: envsentry scan --format json > audit-results.json
      
      - name: Upload audit results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: envsentry-audit
          path: audit-results.json

  test:
    name: Run Tests
    needs: env-audit
    runs-on: ubuntu-latest
    
    steps:
      # ... test steps ...
```

### GitLab CI/CD

**`.gitlab-ci.yml`**:

```yaml
stages:
  - audit
  - test
  - deploy

env-audit:
  stage: audit
  image: python:3.11
  script:
    - pip install envsentry
    - envsentry scan
  artifacts:
    reports:
      junit: audit-results.xml
    paths:
      - audit-results.json
```

### CircleCI

**`.circleci/config.yml`**:

```yaml
version: 2.1

jobs:
  env-audit:
    docker:
      - image: python:3.11
    steps:
      - checkout
      - run:
          name: Install EnvSentry
          command: pip install envsentry
      - run:
          name: Run environment audit
          command: envsentry scan
      - store_artifacts:
          path: audit-results.json

workflows:
  main:
    jobs:
      - env-audit
      - test:
          requires:
            - env-audit
```

## Example 5: Strict Mode for Pre-commit Hooks

### Scenario

Use EnvSentry as a pre-commit hook to prevent committing invalid configurations.

### Pre-commit Hook Setup

**`.pre-commit-config.yaml`**:

```yaml
repos:
  - repo: local
    hooks:
      - id: envsentry
        name: EnvSentry Configuration Audit
        entry: envsentry scan
        language: system
        pass_filenames: false
        always_run: true
```

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

### Git Hook (Manual)

**`.git/hooks/pre-commit`**:

```bash
#!/bin/bash

# Run EnvSentry audit
echo "Running EnvSentry configuration audit..."
envsentry scan

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ EnvSentry audit failed. Please fix configuration issues before committing."
    echo ""
    exit 1
fi

echo "✓ EnvSentry audit passed"
exit 0
```

Make executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Testing the Hook

```bash
# Try to commit with invalid config
echo "PORT=invalid" >> .env
git add .env
git commit -m "test"

# EnvSentry will prevent commit:
# ❌ EnvSentry audit failed. Please fix configuration issues before committing.
```

## Example 6: JSON Output for Tooling Integration

### Scenario

Integrate EnvSentry results into custom tooling, dashboards, or reporting systems.

### Generate JSON Report

```bash
envsentry scan --format json > audit-results.json
```

### JSON Output Format

**Success (no issues)**:

```json
{
  "tool_version": "1.0.0",
  "scan_timestamp": "2024-11-14T10:30:00.000000+00:00",
  "project_path": "/path/to/project",
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

**With findings**:

```json
{
  "tool_version": "1.0.0",
  "scan_timestamp": "2024-11-14T10:30:00.000000+00:00",
  "project_path": "/path/to/project",
  "summary": {
    "total_findings": 2,
    "by_severity": {
      "error": 1,
      "warning": 1,
      "info": 0
    }
  },
  "findings": [
    {
      "code": "ENV009",
      "severity": "error",
      "variable": "SECRET_KEY",
      "message": "Variable 'SECRET_KEY' is too short (minimum length: 50)",
      "location": {
        "file": ".env",
        "line": 2
      },
      "remediation": "Ensure SECRET_KEY has at least 50 characters"
    },
    {
      "code": "ENV008",
      "severity": "warning",
      "variable": "API_KEY",
      "message": "Variable 'API_KEY' appears to contain a placeholder value",
      "location": {
        "file": ".env",
        "line": 5
      },
      "remediation": "Replace the placeholder in API_KEY with an actual value"
    }
  ]
}
```

### Python Integration

```python
import json
import subprocess
import sys

def run_envsentry_audit(project_path: str) -> dict:
    """Run EnvSentry and return parsed results."""
    result = subprocess.run(
        ["envsentry", "scan", "--path", project_path, "--format", "json"],
        capture_output=True,
        text=True
    )
    
    return {
        "exit_code": result.returncode,
        "results": json.loads(result.stdout) if result.stdout else None,
        "error": result.stderr if result.stderr else None
    }

# Run audit
audit = run_envsentry_audit("/path/to/project")

# Check results
if audit["exit_code"] == 0:
    print("✓ Audit passed")
elif audit["exit_code"] == 1:
    print(f"✗ Audit failed with {audit['results']['summary']['total_findings']} findings")
    for finding in audit["results"]["findings"]:
        print(f"  - {finding['code']}: {finding['message']}")
else:
    print(f"✗ Execution error: {audit['error']}")
    sys.exit(2)
```

### Node.js Integration

```javascript
const { execSync } = require('child_process');

function runEnvSentryAudit(projectPath) {
  try {
    const output = execSync(
      `envsentry scan --path ${projectPath} --format json`,
      { encoding: 'utf-8' }
    );
    
    return {
      success: true,
      results: JSON.parse(output)
    };
  } catch (error) {
    if (error.stdout) {
      return {
        success: false,
        results: JSON.parse(error.stdout)
      };
    }
    
    return {
      success: false,
      error: error.message
    };
  }
}

// Run audit
const audit = runEnvSentryAudit('/path/to/project');

if (audit.success) {
  console.log('✓ Audit passed');
} else if (audit.results) {
  console.log(`✗ Found ${audit.results.summary.total_findings} issues`);
  audit.results.findings.forEach(finding => {
    console.log(`  - ${finding.code}: ${finding.message}`);
  });
} else {
  console.error('✗ Execution error:', audit.error);
  process.exit(2);
}
```

### Dashboard Integration

Send results to monitoring dashboard:

```python
import requests
import subprocess
import json

def send_to_dashboard(project_name: str, audit_results: dict):
    """Send audit results to monitoring dashboard."""
    dashboard_url = "https://dashboard.example.com/api/audits"
    
    payload = {
        "project": project_name,
        "timestamp": audit_results["scan_timestamp"],
        "passed": audit_results["summary"]["total_findings"] == 0,
        "findings": audit_results["findings"]
    }
    
    response = requests.post(
        dashboard_url,
        json=payload,
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    response.raise_for_status()

# Run audit and send results
result = subprocess.run(
    ["envsentry", "scan", "--format", "json"],
    capture_output=True,
    text=True
)

audit_results = json.loads(result.stdout)
send_to_dashboard("my-app", audit_results)
```

## Common Patterns

### Development vs Production Config

Use different `.env` files:

```bash
# Development
envsentry scan --env-file .env.development

# Production (in CI)
envsentry scan --env-file .env.production
```

### Multiple Environments

```toml
# .envsentry.toml
[variables.ENVIRONMENT]
type = "string"
required = true
choices = ["development", "staging", "production"]

[variables.DEBUG]
type = "boolean"
required = true

[variables.LOG_LEVEL]
type = "string"
required = true
choices = ["debug", "info", "warn", "error"]
```

### Microservices

Each service has its own `.envsentry.toml`:

```
project/
├── service-a/
│   ├── .env
│   └── .envsentry.toml
├── service-b/
│   ├── .env
│   └── .envsentry.toml
└── .github/
    └── workflows/
        └── ci.yml
```

CI runs audit for each service:

```yaml
- name: Audit Service A
  run: envsentry scan --path service-a

- name: Audit Service B
  run: envsentry scan --path service-b
```

## Troubleshooting

### Exit Codes

- **0**: Audit passed, no issues
- **1**: Audit failed, configuration issues found
- **2**: Execution error (invalid config, file not found)

### Common Issues

**Issue**: `Configuration file not found`

```bash
# Solution 1: Create config
envsentry init

# Solution 2: Specify path
envsentry scan --config /path/to/.envsentry.toml
```

**Issue**: `False positive placeholder warning`

```
ENV008: Variable 'SERVICE_NAME' appears to contain a placeholder value
```

Solution: This is a warning, not an error. Document that it's expected or adjust the value slightly if possible.

**Issue**: Scan succeeds locally but fails in CI

- Ensure `.envsentry.toml` is committed
- Check that `.env.example` exists if `require_example_file = true`
- Verify file paths are relative to project root

## Additional Resources

- [Configuration Reference](configuration.md)
- [Validation Rules](rules.md)
- [Security Documentation](security.md)
- [Example Projects](../examples/)
