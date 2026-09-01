# Install with Docker Compose

Docker Compose is the standard way to run OpenEA Community 1.5.2.

## Requirements

You need:

- Docker Engine
- Docker Compose plugin
- A host capable of running three containers: PostgreSQL, OpenEA web, and OpenEA worker

The application itself supports Python 3.10+, but Python does not need to be installed on the host when you use Docker.

## 1. Obtain the source

Clone or download the OpenEA Community repository, then change into its root directory.

```bash
git clone https://github.com/openeadev/openea-community.git
cd openea-community
```

## 2. Create environment configuration

The Docker Compose file supports sensible local defaults, but you should set a strong session secret and database password before any real deployment.

Create a `.env` file in the repository root:

```dotenv
APP_NAME=OpenEA Community
PAGE_TITLE=OpenEA Community
ENVIRONMENT=production
LOG_LEVEL=INFO
BASE_URL=http://localhost:8000
SESSION_MAX_AGE_SECONDS=28800

SECRET_KEY=replace-with-a-long-random-secret

POSTGRES_DB=openea
POSTGRES_USER=openea
POSTGRES_PASSWORD=replace-with-a-strong-database-password

OPENEA_PORT=8000
```

Generate a suitable application secret with Python if available:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

!!! warning "Production secrets"
    Do not use the placeholder `SECRET_KEY` or database password in a production environment. Do not commit `.env` to source control.

## 3. Start OpenEA

```bash
docker compose up -d --build
```

The Compose stack starts:

```text
postgres
   ▲
   │
   ├──────── web
   │
   └──────── worker
```

The web container runs these startup steps before serving requests:

```text
alembic upgrade head
python -m app.cli seed-system
uvicorn app.main:app ...
```

The worker waits for the web health check before it begins processing queued analytics and findings jobs.

## 4. Verify the deployment

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
docker compose exec web alembic current
```

For OpenEA Community 1.5.2, the expected Alembic head is:

```text
0016_phase15 (head)
```

`/health` verifies that the application process is running. `/health/ready` also checks database connectivity.

## 5. Create the initial administrator

Open:

```text
http://localhost:8000/setup
```

Create the first **Platform Administrator** account.

You can alternatively create the account from the CLI:

```bash
docker compose exec web python -m app.cli create-admin \
  --username admin \
  --display-name "OpenEA Administrator"
```

The CLI prompts for a password. Passwords must be at least 12 characters.

## 6. Sign in

Open:

```text
http://localhost:8000/login
```

Use the administrator account you created.

A Platform Administrator manages users and service accounts, but that role is intentionally not an automatic architecture-repository superuser. If the same person will create and maintain architecture data, assign that user the **Architecture Administrator** or **Architect** role as well.

## 7. Optional: load Northstar Financial demo data

After at least one active user exists:

```bash
docker compose exec web python -m app.cli seed-demo
docker compose exec web python -m app.cli recalculate-metrics-now
docker compose exec web python -m app.cli evaluate-findings-now
```

The demo creates a coherent but intentionally imperfect fictional architecture repository tagged `OpenEA Demo`.

To archive the active demo records later:

```bash
docker compose exec web python -m app.cli remove-demo
```

## 8. Production considerations

Before exposing OpenEA outside a local network:

- Put OpenEA behind HTTPS.
- Set `BASE_URL` to the public HTTPS URL so session cookies receive the Secure flag.
- Use a long, stable `SECRET_KEY`.
- Protect PostgreSQL from untrusted networks.
- Keep `DEBUG=false`.
- Back up PostgreSQL regularly.
- Keep the worker running so analytics and findings stay current.

Continue with [First Login and Setup](first-login.md).
