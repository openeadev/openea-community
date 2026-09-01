# CLI Commands

OpenEA Community administration commands are exposed through:

```bash
python -m app.cli <command>
```

In Docker, prefix commands with:

```bash
docker compose exec web
```

## create-admin

Create the initial Platform Administrator from the terminal:

```bash
python -m app.cli create-admin \
  --username admin \
  --display-name "OpenEA Administrator"
```

The command securely prompts for a password and confirmation.

## seed-system

Seed the standard metamodel and reference data idempotently:

```bash
python -m app.cli seed-system
```

## seed-demo

Seed the fictional Northstar Financial repository:

```bash
python -m app.cli seed-demo
```

The command requires at least one active user because demo changes are audited to an actor.

## remove-demo

Archive active records tagged as OpenEA demo data:

```bash
python -m app.cli remove-demo
```

This archives demo objects and related demo relationships rather than hard-deleting history.

## recalculate-metrics

Queue normal background metric recalculation:

```bash
python -m app.cli recalculate-metrics
```

This is a one-time administrative request. The command does not run on an interval. Platform Administrators configure periodic metrics processing in **Management → Background Processing**.

## recalculate-metrics-now

Run metric calculation synchronously:

```bash
python -m app.cli recalculate-metrics-now
```

Use this for administrative verification and troubleshooting. It runs in the current CLI process and bypasses the asynchronous worker queue. It is not a scheduled command.

## evaluate-findings

Queue finding evaluation:

```bash
python -m app.cli evaluate-findings
```

This is a one-time administrative request. The command does not run on an interval. Platform Administrators configure periodic findings processing in **Management → Background Processing**.

## evaluate-findings-now

Run finding evaluation synchronously:

```bash
python -m app.cli evaluate-findings-now
```

Use this for direct administrative verification or troubleshooting. It runs immediately in the CLI process and is not part of the periodic scheduler.
