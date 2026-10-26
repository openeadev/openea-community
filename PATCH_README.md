# OpenEA Community 1.5.3 Milestone 1 Patch

This patch is intended to be overlaid on the current OpenEA Community 1.5.2 `main` baseline.

It starts the 1.5.3 customer-readiness work by implementing **Administrator Account Recovery** and by recording all six agreed 1.5.3 deliverables in `RELEASE_1_5_3.md`.

## Files in this patch

Replace:

- `app/cli.py`
- `app/services/auth_service.py`
- `docs/reference/cli.md`
- `mkdocs.yml`

Add:

- `tests/test_admin_recovery.py`
- `docs/administration/account-recovery.md`
- `RELEASE_1_5_3.md`

No files should be removed.

## Test

From the repository root:

```bash
ruff check .
python -m pytest
make docs-build
```

## Manual verification

```bash
docker compose exec web python -m app.cli reset-admin-password --username admin
```

Then sign in with the new password and verify access to Management.

## Versioning note

This milestone intentionally does **not** change `pyproject.toml` or `app/core/config.py` from 1.5.2 yet. The runtime should move to 1.5.3 only when the planned 1.5.3 work is ready to be treated as a release candidate.
