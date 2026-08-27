# Worker and Background Calculations

OpenEA persists analytics and findings and updates them using a PostgreSQL-backed job queue.

## Why a worker exists

Repository writes can affect many calculated values. OpenEA avoids recalculating all metrics inside the user's web request.

Instead:

```text
Repository write
      ↓
Queue job in PostgreSQL
      ↓
Worker claims job
      ↓
Calculate persisted metrics / findings
      ↓
Mark job complete
```

## Standard Docker deployment

Docker Compose runs separate `web` and `worker` containers that share the same codebase and PostgreSQL database.

The worker process is:

```bash
python -m app.workers.metrics_worker
```

The worker polls approximately every two seconds when idle.

## Job types

The 1.5.2 worker processes:

- Metrics recalculation
- Finding evaluation

Metrics jobs run `AnalyticsService.calculate_all()`. Finding jobs run `FindingsService.evaluate_all()`.

PostgreSQL row locking and `SKIP LOCKED` are used to claim jobs safely without Redis, Celery, RabbitMQ, or another broker.

## Administrative commands

Queue normal worker processing:

```bash
python -m app.cli recalculate-metrics
python -m app.cli evaluate-findings
```

Run synchronously for verification or troubleshooting:

```bash
python -m app.cli recalculate-metrics-now
python -m app.cli evaluate-findings-now
```

## Render demo deployment

The OpenEA public demo uses a free Render web service, which does not provide a separate free background-worker service. The demo startup script therefore runs the existing worker as a second process in the same web container.

This is appropriate for the small public demo. The standard self-hosted production model remains separate web and worker containers.

## Troubleshooting stale calculations

If repository changes are visible but metrics/findings do not update:

1. Confirm the worker process is running.
2. Review worker logs for failed jobs.
3. Run the synchronous CLI commands above.
4. Confirm PostgreSQL is reachable.
5. Do not replace the worker with web-request calculations as a troubleshooting workaround.
