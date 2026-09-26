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
- `OPENEA_IMAGE`

## Background-processing schedules

Analytics & Metrics and Findings Evaluation intervals are **not** environment variables. They are platform settings stored in PostgreSQL and maintained by a Platform Administrator under **Management → Background Processing**.

This keeps operational scheduling editable without changing container environment configuration. See [Worker and Background Calculations](worker-jobs.md).

## Optional login reCAPTCHA

OpenEA can protect the browser login form with Google reCAPTCHA v2 using the visible **I'm not a robot** checkbox. This protection is disabled by default.

The key material is deployment configuration:

```dotenv
RECAPTCHA_SITE_KEY=<site-key>
RECAPTCHA_SECRET_KEY=<secret-key>
```

The site key is sent to the browser when the feature is enabled. The secret key is used only by the OpenEA backend for verification and is never stored in PostgreSQL or displayed in the administration UI.

After both environment variables are configured, a Platform Administrator can enable or disable the login challenge under **Management → Settings**. The enabled/disabled choice is stored in PostgreSQL; the keys remain environment variables.

When reCAPTCHA is disabled, OpenEA does not load Google reCAPTCHA JavaScript and does not call Google's verification service. Leave the feature disabled for offline or air-gapped deployments.
