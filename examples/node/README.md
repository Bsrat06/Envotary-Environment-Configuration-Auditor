# Node.js Example

This example demonstrates Envotary configuration for a typical Node.js/Express project.

## Files

- `.env.example` - Template for Node.js environment variables
- `.env` - Actual environment file (contains one intentional issue for demonstration)
- `.envotary.toml` - Node.js-specific validation rules

## Variables

- `NODE_ENV` - Node environment (development, production, test)
- `PORT` - Server port number
- `DATABASE_URL` - Database connection string, marked as secret
- `JWT_SECRET` - JWT signing secret, marked as secret
- `API_BASE_URL` - Base URL for external API

## Running Envotary

From the repository root:

```bash
envotary scan --path examples/node
```

This example includes a placeholder value in `.env` for JWT_SECRET to demonstrate placeholder detection.
