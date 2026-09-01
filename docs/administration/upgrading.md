# Upgrading OpenEA Community

OpenEA uses Alembic migrations and is designed for in-place upgrades. Do not recreate the PostgreSQL database for a normal version upgrade.

## General procedure

1. Read the release notes for the target version.
2. Back up PostgreSQL.
3. Preserve the existing `.env` file and PostgreSQL volume.
4. Replace or update the application source.
5. Rebuild and restart containers.
6. Allow the web startup process to run `alembic upgrade head` and `seed-system`.
7. Verify the reported Alembic head.
8. Verify health endpoints, login, worker activity, and important repository views.

Typical Docker commands:

```bash
docker compose build --no-cache
docker compose up -d
docker compose exec web alembic current
```

## Upgrade from 1.5.1 to 1.5.2

OpenEA Community 1.5.2 establishes the independent Community distribution baseline. Later 1.5.2 maintenance updates add the background-processing scheduler through migration `0016_phase15`.

Current Alembic head:

```text
0016_phase15 (head)
```

Existing architecture objects, relationships, users, API tokens, findings, metrics, audit history, and configuration remain compatible. Migration `0016_phase15` adds only the scheduler settings table and its two default schedules.

The Python distribution name becomes `openea-community`, while Python imports and runtime commands continue to use the `app` package.

## Never remove the database volume casually

This command destroys the PostgreSQL volume:

```bash
docker compose down -v
```

Use it only when you intentionally want a completely clean installation.
