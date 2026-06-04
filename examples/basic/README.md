# Basic Example

This is a minimal example demonstrating Envotary's core functionality.

## Files

- `.env.example` - Template showing required environment variables
- `.env` - Actual environment file with values
- `.envotary.toml` - Configuration defining validation rules

## Variables

- `API_KEY` - String type, marked as secret, minimum 10 characters
- `DATABASE_URL` - URL type, marked as secret
- `DEBUG` - Boolean type
- `PORT` - Integer type with valid range 1024-65535
- `ENVIRONMENT` - String type with allowed choices

## Running Envotary

From the repository root:

```bash
envotary scan --path examples/basic
```

This will validate that:
- All required variables are present in `.env`
- Values match their expected types
- No placeholder values remain
- No duplicate variable definitions exist
