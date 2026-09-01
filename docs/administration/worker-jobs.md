# Worker and Background Calculations

OpenEA persists analytics and findings and updates them with a PostgreSQL-backed job queue. OpenEA Community 1.5.2 uses **two complementary triggers** for that queue:

1. **Event-driven processing** after relevant repository changes.
2. **Platform Administrator-controlled schedules** so time-dependent calculations are refreshed even when no one changes repository data.

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

The worker also checks the configured periodic schedules:

```text
Platform Administrator schedule
      ↓
Worker checks due schedules
      ↓
Queue normal background job
      ↓
Worker processes the job
```

The scheduler does **not** execute shell commands or bypass the job queue. Scheduled runs use the same services and worker path as repository-triggered runs.

## Why periodic processing is needed

Some architecture conditions can change because time passes even when the repository itself is unchanged. Examples include:

- review freshness and overdue review dates
- technology vendor-support dates
- lifecycle/support-horizon calculations
- findings driven by date thresholds

Without a periodic schedule, those conditions could remain stale until another repository write happened or an administrator manually queued a recalculation.

## Standard Docker deployment

Docker Compose runs separate `web` and `worker` containers that share the same codebase and PostgreSQL database.

The worker process is:

```bash
python -m app.workers.metrics_worker
```

The worker polls the PostgreSQL job queue approximately every **two seconds** when idle. This does **not** mean calculations run every two seconds; it only means the worker checks for queued work.

The worker checks scheduled processing approximately every **60 seconds**.

## Scheduled processes

OpenEA Community 1.5.2 provides two separately configurable schedules:

| Process | Default | Purpose |
| --- | --- | --- |
| Analytics & Metrics | Enabled, every 6 hours | Recalculate persisted architecture metrics, including date-dependent inputs. |
| Findings Evaluation | Enabled, every 1 hour | Reevaluate built-in and custom findings, including date-threshold rules. |

Metrics recalculation also queues findings evaluation as part of the normal dependency between analytics and findings. The separate Findings schedule allows findings to be reevaluated more frequently without recalculating every metric.

## Configure schedules in the UI

Only a **Platform Administrator** can change these settings.

Open:

**Management → Background Processing**

For each process you can:

- enable or disable periodic processing
- select a controlled interval
- save the schedule
- select **Run now** to queue the process immediately
- see the last queued time
- see the last completed time
- see the next scheduled time
- see the latest execution status and result count
- see the latest error when processing failed

Supported intervals are:

- 15 minutes
- 30 minutes
- 1 hour
- 2 hours
- 4 hours
- 6 hours
- 12 hours
- 24 hours

The interval is intentionally selected from a controlled list. OpenEA Community 1.5.2 does not accept arbitrary cron expressions or arbitrary commands from the UI.

## Run now

**Run now** queues the same normal background job used elsewhere in OpenEA. It does not calculate synchronously inside the browser request.

For example:

```text
Platform Administrator selects Run now
              ↓
OpenEA queues recalculate_all_metrics
              ↓
Worker claims the job
              ↓
AnalyticsService.calculate_all()
```

This keeps browser behavior and scheduled behavior on the same execution path.

## What happens after downtime?

If OpenEA is stopped when a scheduled process becomes due, it does not replay every missed interval.

When the worker returns:

1. It detects that the schedule is overdue.
2. It queues the process **once**.
3. It calculates the next run from the current time using the configured interval.

For example, if a six-hour schedule was missed while OpenEA was offline for 18 hours, OpenEA runs one overdue recalculation after startup rather than three consecutive recalculations.

## Multiple workers

On PostgreSQL, due schedule rows are claimed using transactional row locking with `SKIP LOCKED`. This prevents multiple workers from independently scheduling the same due process at the same time.

Normal queued jobs use the existing PostgreSQL worker locking in the same way.

## Job types

The 1.5.2 worker processes:

- `recalculate_all_metrics`
- `evaluate_findings`

Metrics jobs run `AnalyticsService.calculate_all()`. Finding jobs run `FindingsService.evaluate_all()`.

## Administrative CLI commands

The CLI remains available for operations and troubleshooting.

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

These CLI commands do **not** run automatically on an interval. The Platform Administrator schedules queue the underlying worker jobs directly.

See [CLI Commands](../reference/cli.md) for the exact command behavior.

## Render demo deployment

The OpenEA public demo uses a free Render web service, which does not provide a separate free background-worker service. The demo startup script therefore runs the existing worker as a second process in the same web container.

The scheduler is part of that worker, so the same Platform Administrator schedules operate in the Render demo.

This arrangement is appropriate for the small public demo. The standard self-hosted production model remains separate web and worker containers.

## Troubleshooting stale calculations

If repository changes are visible but metrics/findings do not update:

1. Open **Management → Background Processing** and review the latest status/error.
2. Confirm the worker process is running.
3. Review worker logs for failed jobs.
4. Use **Run now** to queue a test execution.
5. If needed, run the synchronous CLI commands for direct administrative verification.
6. Confirm PostgreSQL is reachable.
7. Do not replace the worker with web-request calculations as a troubleshooting workaround.
