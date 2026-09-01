# Public Demo Deployment on Render

OpenEA Community's public demonstration environment can run on Render using a web service and PostgreSQL. This deployment pattern is intended for a **disposable public demo**, not as the recommended production architecture for organizations self-hosting OpenEA.

The standard production/self-hosted model remains Docker Compose with separate web and worker containers. See [Install with Docker Compose](../getting-started/installation.md).

## Demo architecture

```text
GitHub main branch
      ↓
GitHub Actions checks
      ↓
Render deployment
      ↓
Render web service ─────► PostgreSQL
   ├── Uvicorn/FastAPI
   └── OpenEA worker
```

The worker runs as a background process in the same Render web container because the public demo is intentionally optimized for a small free-tier footprint.

## Deployment sequence

The demo startup sequence is:

```text
alembic upgrade head
      ↓
commit-aware demo reset check
      ↓
reset/reseed only for a new deployed commit
      ↓
start OpenEA worker in background
      ↓
exec Uvicorn as the main process
```

Uvicorn must remain the main container process so Render can detect and supervise the listening web port.

A minimal startup pattern is:

```sh
python -m app.workers.metrics_worker &
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
```

## Commit-aware demo reset

The public demo is editable, so visitors can create, edit, and archive architecture records. OpenEA's demo startup script uses Render's deployed Git commit identifier to distinguish a new application deployment from a normal cold start/restart.

Expected behavior:

- Same deployed commit: preserve current demo changes.
- New deployed commit: reset the demo repository and reseed Northstar Financial.
- Forced demo reset: an administrator can intentionally request a reset for the same commit using the configured demo-control setting.

This prevents a free-service wake-up or normal restart from erasing user changes while still ensuring each new release starts from a known demo baseline.

## Database URL

Render may provide a PostgreSQL URL such as:

```text
postgresql://user:password@host/database
```

OpenEA normalizes supported `postgresql://` and legacy `postgres://` values to the SQLAlchemy Psycopg 3 dialect:

```text
postgresql+psycopg://...
```

The same normalization is used by the application and Alembic.

## Health check

Use:

```text
/health/ready
```

as the Render health-check path. This confirms both the FastAPI process and database connectivity.

## Background calculations

The same worker used in Docker Compose runs in the Render web container. It processes event-driven jobs and the Platform Administrator schedules configured under **Management → Background Processing**.

Default schedules are:

- Analytics & Metrics: every 6 hours
- Findings Evaluation: every 1 hour

See [Worker and Background Calculations](worker-jobs.md).

## Environment variables

The demo deployment uses the normal OpenEA configuration plus demo-specific controls such as:

- `DEMO_RESET_ON_DEPLOY`
- `DEMO_FORCE_RESET`
- `DEMO_ADMIN_PASSWORD`
- `DEMO_USER_PASSWORD`

Secrets and the database connection string should be managed through Render rather than committed to the repository.

See [Environment Variables](../reference/configuration.md).

## Automatic deployment from GitHub

The intended flow is:

```text
commit / merge to main
      ↓
GitHub Actions
      ↓
checks pass
      ↓
Render automatically deploys
```

The Blueprint can use Render's checks-pass deployment trigger so a failed GitHub Actions run does not replace the working demo.

## Custom domain

The public demo can be exposed through:

```text
https://demo.openea.dev
```

Configure the custom domain in Render after the generated Render URL works, then add the DNS record requested by Render and allow TLS provisioning to complete.

## Free-tier expectations

Treat free-tier demo infrastructure as disposable. Service sleep/cold starts, database limits, and provider retention policies can change over time. Do not use the public demo as a production system or as the only copy of architecture data.
