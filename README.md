# OpenEA Community

OpenEA Community is a self-hosted, open-source enterprise architecture knowledge and decision-support platform. Version **1.5.2** establishes the independent Community distribution baseline, with Community-specific package identity and release hygiene while preserving all 1.5.1 application behavior and database compatibility.

OpenEA Community is repository-first: architecture objects and governed relationships are authoritative, while search, impact analysis, risk, findings, portfolios, capability maps, and roadmaps are derived from that repository. OpenEA Community is licensed under the GNU Affero General Public License v3.0; see `LICENSE`.

## MVP capabilities

OpenEA Community 1.0 includes the 12 standard enterprise architecture object types, governed relationship rules, schema-validated flexible metadata, local authentication and five application roles, repository CRUD and archival, PostgreSQL full-text/fuzzy search, governance and ADR workflows, reviews, comments, immutable audit history, recursive impact analysis, explainable risk/data-quality metrics, a declarative findings engine, Application and Technology portfolios, capability maps, derived roadmaps, CSV import/export, and versioned REST endpoints under `/api/v1`.

The runtime remains intentionally small: Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL 16+, Jinja2, HTMX, Tabler/Bootstrap, a PostgreSQL-backed worker queue, and Docker Compose. It does not require Redis, Celery, Kafka, Elasticsearch, Neo4j, Node.js, a JavaScript SPA framework, cloud SaaS, or AI.

## Docker installation

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
# Put the generated value in SECRET_KEY in .env.

docker compose up -d --build
```

The web container automatically runs Alembic migrations and idempotent system seeding before it begins serving traffic. The worker waits for the web health check, so it does not access job tables before migrations complete.

Verify:

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
docker compose exec web alembic current
```

Expected migration head: `0016_phase15`.

Browse to `http://localhost:8000/setup` to create the initial Platform Administrator.

## Optional demo repository

After creating an administrator, seed the fictional Northstar Financial repository:

```bash
docker compose exec web python -m app.cli seed-demo
docker compose exec web python -m app.cli recalculate-metrics
docker compose exec web python -m app.cli evaluate-findings
```

Demo records are tagged `OpenEA Demo`. Remove the active demo repository without deleting history:

```bash
docker compose exec web python -m app.cli remove-demo
```

## Background processing

OpenEA recalculates analytics and findings after relevant repository changes and also supports Platform Administrator-controlled periodic schedules for time-dependent calculations. The default schedules are metrics every six hours and findings every hour.

Platform Administrators manage these schedules under **Management → Background Processing**, where each process can be enabled/disabled, assigned a controlled interval, or queued immediately with **Run now**. The background worker checks due schedules approximately once per minute and the normal PostgreSQL job queue approximately every two seconds when idle.

The manual CLI commands remain available for operations and troubleshooting; they are not the scheduler itself. See the [Worker and Background Calculations](docs/administration/worker-jobs.md) documentation for details.

## CSV and API

Architects and Architecture Administrators can use `/imports` for the CSV upload → map → validate → preview → commit workflow. Filtered repository export is available from `/exports/objects.csv`.

Interactive OpenAPI documentation is at `/docs`; the versioned API starts at `/api/v1`. API requests may use an authenticated OpenEA Community browser session or `Authorization: Bearer <token>`. Bearer requests must satisfy both the identity's application roles and the token's endpoint scope. Users manage PATs at `/account/tokens`; Platform Administrators manage service accounts at `/admin/service-accounts` and can revoke tokens at `/admin/api-tokens`.

## Development and verification

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
python -m pytest
```

For live Playwright checks:

```bash
playwright install chromium
OPENEA_E2E_BASE_URL=http://localhost:8000 \
OPENEA_E2E_USERNAME=architect \
OPENEA_E2E_PASSWORD='your-password' \
pytest tests/e2e -q
```

## Documentation

The OpenEA Community documentation is built with [MkDocs](https://www.mkdocs.org/) and Material for MkDocs. The Markdown source is stored in `docs/`, the site configuration is in `mkdocs.yml`, and the documentation-only Python dependency is declared in `requirements-docs.txt`.

Published documentation is available at **https://docs.openea.dev/**. The documentation source lives in this repository so application and documentation changes can be reviewed and released together.

### Install the documentation tooling

From an activated development virtual environment:

```bash
python -m pip install -r requirements-docs.txt
```

### Preview the documentation locally

Start MkDocs in the background:

```bash
make docs
```

By default, the documentation is available at:

```text
http://127.0.0.1:8001/
```

`make docs` writes the MkDocs process ID to `.mkdocs.pid` and its output to `.mkdocs.log`. Both files are ignored by Git.

Check whether the documentation server is running:

```bash
make docs-status
```

Stop it when finished:

```bash
make docs-stop
```

If port 8000 is already being used by the OpenEA application, override the documentation port:

```bash
make docs DOCS_PORT=8001
make docs-status DOCS_PORT=8001
make docs-stop
```

You can also override the bind address:

```bash
make docs DOCS_HOST=0.0.0.0 DOCS_PORT=8001
```

### Validate a documentation build

Before committing documentation changes, run:

```bash
make docs-build
```

This executes:

```bash
mkdocs build --strict
```

and fails if MkDocs reports build warnings or errors. The generated `site/` directory is a local build artifact and is not committed.

### Update and publish documentation

1. Edit or add Markdown under `docs/`.
2. Update `mkdocs.yml` when adding a page that should appear in navigation.
3. Run `make docs` and review the changes locally.
4. Run `make docs-build`.
5. Commit the documentation source, `mkdocs.yml`, and any related application changes.
6. Push or merge to `main`.

The GitHub Pages documentation workflow builds the MkDocs site and publishes it to `https://docs.openea.dev/`. Do not commit the generated `site/` directory.

For detailed product documentation, tutorials, administration guidance, and reference material, use the published documentation site rather than duplicating that material in this README.

## UI branding

See `docs/ui-branding.md` for the 1.2.0 Tabler shell, theme behavior, and placeholder asset paths.


## Relationship CSV Import

Version 1.4.0 adds a separate relationship import workflow under **Import**. Relationship endpoints are resolved deterministically by UUID, external ID when available, exact name, then alias. Ambiguous rows remain errors until corrected. See `RELEASE_1_4_0.md` and `examples/relationship-import.csv`.

## Custom finding rules

Version 1.5.2 is the first independently maintained OpenEA Community baseline. It preserves the 1.5.1 findings and Repository Health behavior, uses the `openea-community` Python distribution name, and adds source/release hygiene files without changing the database schema. See `RELEASE_1_5_2.md`, `RELEASE_1_5_1.md`, `docs/findings.md`, and `docs/analytics.md`.
