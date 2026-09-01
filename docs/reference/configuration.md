# Environment Variables

OpenEA Community reads configuration from environment variables. Variables are case-insensitive in the Pydantic Settings layer.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `OpenEA Community` | Product name shown in the UI. |
| `APP_VERSION` | `1.5.2` | Application version string. |
| `PAGE_TITLE` | `OpenEA Community` | Browser/page title branding. |
| `ENVIRONMENT` | `development` | Runtime environment label. |
| `DEBUG` | `false` | FastAPI debug mode. Keep disabled in production. |
| `LOG_LEVEL` | `INFO` | Application log level. |
| `DATABASE_URL` | local PostgreSQL Psycopg URL | SQLAlchemy connection URL. |
| `SECRET_KEY` | development placeholder | Signs browser sessions. Replace for real deployments. |
| `BASE_URL` | `http://localhost:8000` | Canonical public application URL. HTTPS enables Secure cookies. |
| `TRUSTED_PROXY_COUNT` | `0` | Trusted-proxy configuration baseline. |
| `SESSION_MAX_AGE_SECONDS` | `28800` | Maximum signed browser-session age. Minimum 300 seconds. |

## Docker Compose variables

Docker Compose additionally recognizes:

| Variable | Default |
| --- | --- |
| `POSTGRES_DB` | `openea` |
| `POSTGRES_USER` | `openea` |
| `POSTGRES_PASSWORD` | `openea` |
| `OPENEA_PORT` | `8000` |

## Render demo variables

The public-demo Blueprint additionally uses:

- `DEMO_RESET_ON_DEPLOY`
- `DEMO_FORCE_RESET`
- `DEMO_ADMIN_PASSWORD`
- `DEMO_USER_PASSWORD`

These are demo-hosting controls rather than requirements for normal self-hosted OpenEA installations.

## Settings stored in PostgreSQL

Not every administrative setting is an environment variable. The periodic **Analytics & Metrics** and **Findings Evaluation** schedules are persisted in `scheduled_job_settings` and maintained through **Management → Background Processing**.
