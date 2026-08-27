# Configuration

OpenEA Community reads infrastructure configuration from environment variables through Pydantic Settings.

For the canonical variable list, see [Environment Variables](../reference/configuration.md).

## Production essentials

At minimum, review these values before production use:

```dotenv
ENVIRONMENT=production
DEBUG=false
BASE_URL=https://architecture.example.com
SECRET_KEY=<long-random-secret>
DATABASE_URL=postgresql+psycopg://...
LOG_LEVEL=INFO
SESSION_MAX_AGE_SECONDS=28800
```

## BASE_URL and cookies

OpenEA automatically enables the Secure flag on browser session cookies when `BASE_URL` starts with `https://`.

Set `BASE_URL` to the actual public URL used by users. Do not leave it at the local default behind a production HTTPS reverse proxy.

## SECRET_KEY

`SECRET_KEY` signs browser sessions.

- Use a long random value.
- Keep it out of source control.
- Keep it stable during normal operation.
- Changing it invalidates existing browser sessions.

## Database URL

The default driver is Psycopg 3:

```text
postgresql+psycopg://user:password@host:5432/database
```

The application and Alembic also normalize Render-style `postgresql://` or legacy `postgres://` URLs to the Psycopg 3 SQLAlchemy dialect.

## Docker Compose variables

The Compose stack additionally uses:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `OPENEA_PORT`
