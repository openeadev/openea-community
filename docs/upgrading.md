# Upgrading OpenEA

## 0.8.0 to 0.9.0

Preserve `.env` and the PostgreSQL volume. Phase 9 creates persisted metrics and the PostgreSQL job queue, and adds a worker service.

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose exec web alembic upgrade head
docker compose exec web alembic current
docker compose exec web python -m app.cli recalculate-metrics
```

Expected head: `0009_phase9`. Verify `web`, `worker`, and `postgres` with `docker compose ps`.


## 0.7.0 to 0.8.0

Preserve `.env` and the PostgreSQL volume. Phase 8 adds no schema tables or columns, but advances the Alembic chain with release marker `0008_phase8`.

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose exec web alembic upgrade head
docker compose exec web alembic current
```

Expected head: `0008_phase8`.

Refresh local development dependencies and verify:

```bash
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
python -m pytest
```

## 0.6.0 to 0.7.0

Preserve `.env` and the PostgreSQL volume, replace the application files, and run:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose exec web alembic upgrade head
docker compose exec web alembic current
```

Expected head: `0007_phase7 (head)`. The migration preserves existing data and creates reviews, comments, and immutable audit history.

## 0.5.0 to 0.6.0

Preserve `.env` and the PostgreSQL volume. Back up PostgreSQL before upgrading.

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose exec web alembic upgrade head
docker compose exec web alembic current
```

Expected head: `0006_phase6`.

The migration enables `pg_trgm` and creates search indexes. It does not recreate or discard repository data.

## 0.9.0 to 0.10.0

Phase 10 adds `rule_definitions` and `findings`. Apply `0010_phase10`, then run the idempotent system seed so the built-in finding rules are installed:

```bash
docker compose exec web alembic upgrade head
docker compose exec web python -m app.cli seed-system
docker compose exec web python -m app.cli evaluate-findings
```

No database recreation is required.

## 0.10.0 to 0.11.0

1. Preserve `.env` and the PostgreSQL volume.
2. Replace application files with the 0.11.0 release.
3. Rebuild and start containers.
4. Run `docker compose exec web alembic upgrade head`.
5. Confirm `0011_phase11 (head)`.
6. Refresh the local editable install and run Ruff and pytest.

Phase 11 has no schema-changing tables; migration `0011_phase11` is a release marker because portfolio and roadmap views derive from existing repository data.

## 0.11.0 to 1.0.0

1. Back up PostgreSQL.
2. Preserve `.env` and the PostgreSQL volume.
3. Replace application files with the 1.0.0 release.
4. Run `docker compose down` followed by `docker compose build --no-cache` and `docker compose up -d`.
5. The web container automatically runs `alembic upgrade head` and `python -m app.cli seed-system` before starting Uvicorn. The worker waits for the web health check.
6. Confirm `docker compose exec web alembic current` reports `0012_phase12 (head)`.
7. Refresh the local editable environment with `python -m pip install -e '.[dev]'`, then run `ruff check .` and `python -m pytest`.
8. Verify `/health`, `/health/ready`, `/imports`, `/docs`, and `/api/v1/`.

No database recreation is required and existing repository data is preserved.


## 1.0.0 to 1.1.0

OpenEA Community 1.1.0 is a maintenance release that fixes clean-install migration compatibility. It does not add a database schema migration; Alembic head remains `0012_phase12`.

1. Preserve `.env` and the PostgreSQL volume.
2. Replace the application files with the 1.1.0 release.
3. Rebuild and restart:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

4. Verify:

```bash
docker compose exec web alembic current
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

A deliberately clean install can use `docker compose down -v` before rebuilding. This destroys the PostgreSQL volume and should only be used when a full reset is intended.

## 1.1.0 to 1.2.0

OpenEA Community 1.2.0 is a UI-only release. There is no database schema migration; Alembic head remains `0012_phase12`.

1. Preserve `.env` and the existing PostgreSQL volume.
2. Replace application files with the 1.2.0 release.
3. Run `docker compose down && docker compose build --no-cache && docker compose up -d`.
4. Verify `docker compose exec web alembic current` reports `0012_phase12 (head)`.
5. Run `ruff check .` and `python -m pytest` locally.
6. Verify the left sidebar, public Sign in action, and light/dark toggle in the browser.

## 1.2.0 to 1.3.0

OpenEA Community 1.3.0 adds scoped API tokens and service accounts. Migration `0013_phase13` adds `users.is_service_account` and the `api_tokens` table.

1. Preserve `.env` and the PostgreSQL volume.
2. Replace application files with the 1.3.0 release.
3. Run `docker compose down && docker compose build --no-cache && docker compose up -d`.
4. Confirm `docker compose exec web alembic current` reports `0013_phase13 (head)`.
5. Sign in and create a PAT at `/account/tokens`, or create a service account at `/admin/service-accounts` as a Platform Administrator.
6. Open `/docs` and verify Swagger UI loads and exposes Bearer authentication.

No existing users or architecture data are recreated or discarded.

## 1.3.0 to 1.4.0

OpenEA Community 1.4.0 adds the separate Relationship CSV Import workflow. Migration `0014_phase14` adds an import-kind discriminator to `import_batches` and permits `object_type_key` to be null for relationship batches.

1. Preserve `.env` and the PostgreSQL volume.
2. Replace application files with the 1.4.0 release.
3. Run `docker compose down && docker compose build --no-cache && docker compose up -d`.
4. Confirm `docker compose exec web alembic current` reports `0014_phase14 (head)`.
5. Refresh the local editable environment and run `ruff check .` and `python -m pytest`.
6. Open `/imports`, upload `examples/relationship-import.csv` after adjusting names to objects that exist in your repository, and verify the map/validate/preview/commit flow.

No architecture objects or existing relationships are recreated or discarded.

## 1.4.0 to 1.5.0

OpenEA Community 1.5.0 adds governed custom declarative finding-rule authoring. Migration `0015_phase15` adds creator/updater attribution and archival metadata to `rule_definitions`; existing rules and findings are preserved.

1. Back up PostgreSQL.
2. Replace application files with the 1.5.0 release.
3. Run `docker compose build --no-cache && docker compose up -d`.
4. Confirm `docker compose exec web alembic current` reports `0015_phase15 (head)`.
5. Sign in as an Architecture Administrator and verify **Finding Rules** can create a custom rule while built-in rules have no Delete action.
6. Run `ruff check .` and `python -m pytest` in the Python 3.10 development environment.


## 1.5.0 to 1.5.1

OpenEA Community 1.5.1 is a UX maintenance release. It requires no database migration. Replace the application files, rebuild/restart the containers, and confirm Alembic remains at `0015_phase15 (head)`. Resolved findings are now hidden by default and Repository Health dimensions have explainable drill-down views.

## 1.5.1 to 1.5.2

OpenEA Community 1.5.2 establishes the independent Community distribution baseline. Current 1.5.2 maintenance includes migration `0016_phase15`, which adds Platform Administrator-controlled scheduled background processing. Existing architecture objects, relationships, users, API tokens, findings, metrics, audit history, and configuration remain compatible.

1. Back up PostgreSQL and preserve the existing `.env` file and PostgreSQL volume.
2. Replace the application files with the current 1.5.2 Community release.
3. Rebuild and restart with `docker compose build --no-cache && docker compose up -d`.
4. Allow the normal startup `alembic upgrade head` to create `scheduled_job_settings`.
5. Confirm `docker compose exec web alembic current` reports `0016_phase15 (head)`.
6. Verify `curl http://localhost:8000/health` reports version `1.5.2`.
7. Sign in as a Platform Administrator and review **Management → Background Processing**.
8. For editable local development, refresh the install with `python -m pip install -e '.[dev]'`. The installed distribution is named `openea-community`; Python imports and runtime commands continue to use the existing `app` package.
9. Run `ruff check .` and `python -m pytest`.

No database recreation is required. Do not remove the PostgreSQL volume during this upgrade.
