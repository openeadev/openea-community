# Local Development

OpenEA Community supports Python 3.10 and later.

## Python environment

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Configure a PostgreSQL database and environment variables, then apply migrations and system seed:

```bash
alembic upgrade head
python -m app.cli seed-system
```

Start the web application:

```bash
uvicorn app.main:app --reload
```

For complete background behavior, run the worker in a second terminal:

```bash
python -m app.workers.metrics_worker
```

## Browser assets for local Python development

The Docker image vendors OpenEA's pinned browser dependencies automatically during `docker build`. If you run Uvicorn directly from a source checkout, populate the local vendor directory once while network access is available:

```bash
python scripts/vendor_frontend_assets.py
```

After that, verify the local copy without making network requests:

```bash
python scripts/vendor_frontend_assets.py --check
```

A direct Python development server can then run without Internet access as long as PostgreSQL and the Python environment are already available locally.

## Development principles

- Keep Python 3.10 compatibility.
- Put business rules in services.
- Use Alembic for database changes.
- Preserve upgrade compatibility; do not instruct users to reset a database for routine changes.
- Keep server-rendered architecture unless a focused JavaScript enhancement solves a specific problem.
