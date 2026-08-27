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

## Development principles

- Keep Python 3.10 compatibility.
- Put business rules in services.
- Use Alembic for database changes.
- Preserve upgrade compatibility; do not instruct users to reset a database for routine changes.
- Keep server-rendered architecture unless a focused JavaScript enhancement solves a specific problem.
