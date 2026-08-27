# Testing

OpenEA Community uses pytest and Ruff for the normal development loop, with Playwright for optional live browser testing.

## Standard checks

```bash
ruff check .
python -m compileall -q app scripts
pytest -q
```

The repository Makefile exposes the same basic flow through:

```bash
make test
```

## Database coverage

The fast automated suite can use SQLite for behavior that is not PostgreSQL-specific. Production remains PostgreSQL 16+.

PostgreSQL-specific features such as full-text search, `pg_trgm`, and job claiming should be verified in appropriate integration/deployment testing.

## Playwright

Install Chromium:

```bash
playwright install chromium
```

Then point the E2E suite at a running OpenEA environment:

```bash
OPENEA_E2E_BASE_URL=http://localhost:8000 \
OPENEA_E2E_USERNAME=architect \
OPENEA_E2E_PASSWORD='your-password' \
pytest tests/e2e -q
```

The live browser suite is opt-in because it requires a running deployment and browser binary.
