# Django Example

This example demonstrates Envotary configuration for a typical Django project.

## Files

- `.env.example` - Template for Django environment variables
- `.env` - Actual environment file (contains one intentional issue for demonstration)
- `.envotary.toml` - Django-specific validation rules

## Variables

- `SECRET_KEY` - Django secret key, minimum 50 characters, marked as secret
- `DEBUG` - Debug mode boolean
- `DATABASE_URL` - Database connection string, marked as secret
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `STATIC_ROOT` - Optional path for static files
- `MEDIA_ROOT` - Optional path for media files

## Running Envotary

From the repository root:

```bash
envotary scan --path examples/django
```

This example includes an intentionally short SECRET_KEY in `.env` to demonstrate validation failures.
