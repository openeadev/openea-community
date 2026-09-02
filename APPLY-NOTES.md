# OpenEA Community 1.5.2 — Offline Runtime Permissions Fix

This corrective overlay fixes a file-permission defect in the prior offline-runtime patch.

## Root cause

The frontend vendoring script downloaded Tabler, HTMX, Lucide, Cytoscape.js,
Swagger UI, and ReDoc using Python `NamedTemporaryFile`.

Those temporary files default to mode `0600`. The Docker build runs as root,
so the downloaded files became root-readable only. OpenEA then starts as the
unprivileged `openea` user and could not serve `/static/vendor/...`.

The old `--check` command only verified that the files existed, so it could
report success even when the application process could not read them.

That is why OpenEA displayed mostly unstyled HTML even though:

```bash
docker compose exec web python scripts/vendor_frontend_assets.py --check
```

reported that the assets were present.

## Permanent fix

- Each downloaded vendor file is normalized to mode `0644`.
- The Dockerfile defensively applies `chmod -R a+rX app/static/vendor`.
- `--check` now verifies that files exist, are non-empty, and can actually be opened.
- Troubleshooting and release documentation are updated.
- No database migration is required.

## Apply

Extract this ZIP over the root of the current OpenEA Community 1.5.2 repository.

Then rebuild the OpenEA image while connected:

```bash
docker compose down
docker compose build --no-cache web
docker compose up -d --no-build
```

Verify:

```bash
docker compose exec web python scripts/vendor_frontend_assets.py --check
docker compose exec web sh -lc 'ls -l app/static/vendor/tabler/tabler.min.css app/static/vendor/tabler/tabler.min.js'
curl -I http://localhost:8000/static/vendor/tabler/tabler.min.css
```

The vendor files should be readable by all users (for example `-rw-r--r--`), and
the CSS request should return HTTP 200.

Then disconnect the machine and hard-refresh OpenEA.

## Immediate workaround for the current running container

Before rebuilding, you can confirm the diagnosis with:

```bash
docker compose exec -u root web chmod -R a+rX /opt/openea/app/static/vendor
```

Refresh the browser afterward. If the styling returns, the permission issue is
confirmed. This workaround does not survive a container/image recreation, so
apply the permanent overlay and rebuild.

## Validation performed

- Python compileall: passed
- pytest: 148 passed, 3 skipped
- git diff --check: passed
- No migration
- Community version remains 1.5.2
