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

`docker-compose.yml` explicitly passes `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET_KEY` from the Compose environment into the `web` container. The worker does not need the reCAPTCHA keys because browser-login verification is handled by the web application.

After changing either key in `.env`, recreate the web container so Compose applies the new environment values:

```bash
docker compose up -d --force-recreate web
```

You can verify that both variables reached the running container without displaying their values:

```bash
docker compose exec web python -c "import os; print('Site key configured:', bool(os.getenv('RECAPTCHA_SITE_KEY'))); print('Secret key configured:', bool(os.getenv('RECAPTCHA_SECRET_KEY')))"
```

Expected output when both are configured:

```text
Site key configured: True
Secret key configured: True
```

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

Use separate Google reCAPTCHA keys for development and production. For local development, create a **Challenge (v2) / checkbox** key whose allowed domain is `localhost`. For the hosted demo or another production deployment, use a different checkbox key restricted to that deployment hostname. Do not add `http://`, `https://`, a port, or a path to the allowed-domain entry.

The site key is sent to the browser when the feature is enabled. The secret key is used only by the OpenEA backend for verification and is never stored in PostgreSQL or displayed in the administration UI.

After both environment variables are configured, a Platform Administrator can enable or disable the login challenge under **Management → Settings**. The enabled/disabled choice is stored in PostgreSQL; the keys remain environment variables.

When reCAPTCHA is disabled, OpenEA does not load Google reCAPTCHA JavaScript and does not call Google's verification service. Leave the feature disabled for offline or air-gapped deployments.
