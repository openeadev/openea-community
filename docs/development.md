# Development

OpenEA Community supports Python 3.10 and later. PostgreSQL 16+ is the production database. SQLite is used by the fast automated unit/integration suite where PostgreSQL-specific behavior is not required.

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
python -m pytest
uvicorn app.main:app --reload
```

Database changes must use Alembic. Do not reset an existing database for normal upgrades. Business rules belong in services rather than route handlers or templates.

Playwright live tests are opt-in because they require a running deployment and browser binary. Install Chromium with `playwright install chromium`, then set `OPENEA_E2E_BASE_URL`, `OPENEA_E2E_USERNAME`, and `OPENEA_E2E_PASSWORD` before running `pytest tests/e2e -q`.
