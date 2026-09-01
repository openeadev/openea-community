# Troubleshooting

This page covers the first checks to perform when OpenEA Community is running but a request, calculation, or repository view does not behave as expected.

## Start with health checks

For Docker Compose deployments:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
docker compose ps
```

`/health` confirms that the FastAPI process is running. `/health/ready` also checks database connectivity.

Confirm the current database migration:

```bash
docker compose exec web alembic current
```

For the current OpenEA Community 1.5.2 maintenance baseline, the expected head is:

```text
0016_phase15 (head)
```

## Use the Request ID when a request fails

OpenEA assigns a Request ID to every HTTP request and returns it in the `X-Request-ID` response header.

If an unexpected browser error occurs, OpenEA displays a branded error page with a Request ID. The page intentionally does not expose a Python traceback, SQL statement, database exception, credentials, or other internal details.

Unexpected API `500` responses return a safe message and `request_id`.

To investigate with Docker Compose, search the web logs for that ID:

```bash
docker compose logs web | grep 'REQUEST-ID-HERE'
```

The matching server-side log entry contains the detailed exception needed by an administrator or developer.

!!! important "Report the Request ID"
    When a user reports an unexpected OpenEA error, ask for the Request ID, the page/action they were using, and the approximate time. Do not ask the user to copy database credentials or internal stack traces from a production system.

## Metrics or findings appear stale

Open **Management → Background Processing** as a Platform Administrator and review:

- whether each schedule is enabled
- last queued time
- last completed time
- next scheduled time
- latest status/result count
- latest error

The worker normally checks queued work about every two seconds and scheduled processing about every 60 seconds.

Also verify the worker:

```bash
docker compose ps
docker compose logs worker
```

Use **Run now** to queue a normal asynchronous test. For direct administrative verification, the synchronous CLI commands are:

```bash
docker compose exec web python -m app.cli recalculate-metrics-now
docker compose exec web python -m app.cli evaluate-findings-now
```

These CLI commands run once; they are not the periodic scheduler.

## A relationship Target Object list is empty

The Target Object list is intentionally dependent on the selected governed relationship rule.

1. Select the relationship type / target-type combination first.
2. OpenEA then loads only non-archived records of that permitted target type.
3. Draft, Active, and Inactive targets are allowed and are sorted alphabetically.

If a valid target still does not appear:

- confirm the target object is not archived
- confirm the selected relationship rule permits that source and target type
- hard-refresh the browser after updating OpenEA static assets
- check the browser console/network log for a failed relationship-target request or blocked script

Do not weaken the Content Security Policy to permit inline JavaScript as a workaround. OpenEA's relationship-form behavior is implemented through its static JavaScript asset.

## An archived object seems to be missing

Normal operational views intentionally focus on current architecture.

To find archived repository records:

1. Open **Explore**.
2. Set **Record status** to **Archived**, or choose **All records**.
3. Open the archived record directly if needed.

On an object's **Relationships** tab, historical relationship entries are hidden by default. Select **Show archived** to reveal both relationships to archived objects and relationship records that were themselves archived.

Authorized users can open an archived object and select **Restore**. Existing relationships were preserved during archival and return to the current-state relationship view automatically after restoration.

## Render demo starts slowly

The public demo uses Render free infrastructure. A deployment can spend time applying migrations, resetting/reseeding the demo repository, and starting the worker before Uvicorn begins accepting traffic. A sleeping free service can also take time to wake.

The Render startup script must leave Uvicorn as the main process and start the worker in the background. The standard self-hosted Docker Compose deployment continues to use separate web and worker containers.

## Documentation checks

Before committing documentation changes:

```bash
make docs-build
```

This runs:

```bash
mkdocs build --strict
```

Use `make docs`, `make docs-status`, and `make docs-stop` for local documentation preview.
