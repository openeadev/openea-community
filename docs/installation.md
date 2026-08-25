# Installation

## Requirements

Docker deployment requires Docker Engine with the Compose plugin. Local development requires Python 3.10+ and PostgreSQL 16+.

## Docker Compose

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
# Set SECRET_KEY in .env to the generated value.
docker compose up -d --build
```

OpenEA Community 1.0 runs `alembic upgrade head` and idempotent system seeding in the web container before Uvicorn starts. The worker waits for the web health check, preventing background jobs from accessing a pre-migration schema.

Verify:

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
docker compose exec web alembic current
```

Expected migration head: `0015_phase15`.

For a new installation, browse to `/setup` and create the initial Platform Administrator. Add an Architecture Administrator or Architect role to accounts that will maintain architecture records.

The first administrator can alternatively be created from the container:

```bash
docker compose exec web python -m app.cli create-admin \
  --username admin \
  --display-name "OpenEA Administrator"
```

## Local development

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
alembic upgrade head
python -m app.cli seed-system
uvicorn app.main:app --reload
```

Verification:

```bash
ruff check .
python -m pytest
```
