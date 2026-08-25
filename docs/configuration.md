# Configuration

OpenEA Community infrastructure configuration is supplied through environment variables. Normal architecture configuration will live in the database in later phases.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `OpenEA Community` | Product name shown in the UI. |
| `PAGE_TITLE` | `OpenEA Community` | Browser/page title branding. |
| `ENVIRONMENT` | `development` | Runtime environment label. |
| `DEBUG` | `false` | FastAPI debug mode. Do not enable in production. |
| `LOG_LEVEL` | `INFO` | Application log level. |
| `BASE_URL` | `http://localhost:8000` | Canonical application base URL. HTTPS automatically enables the Secure flag on session cookies. |
| `SECRET_KEY` | development placeholder | Signs browser sessions. Replace with a long random secret before real use. |
| `DATABASE_URL` | local PostgreSQL URL | SQLAlchemy database URL. |
| `SESSION_MAX_AGE_SECONDS` | `28800` | Maximum signed browser-session age in seconds. Minimum 300. |
| `TRUSTED_PROXY_COUNT` | `0` | Reserved trusted-proxy configuration baseline. Forwarded headers are not trusted merely because they are present. |

Docker Compose also accepts `OPENEA_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.

Changing `SECRET_KEY` invalidates existing browser sessions. Keep it secret and stable unless session invalidation is intentional.
