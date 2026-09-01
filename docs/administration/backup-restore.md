# Backup and Restore

PostgreSQL is OpenEA Community's authoritative persistent store. Back it up before upgrades, large imports, and other significant repository changes.

## Docker backup

For the default Docker Compose configuration:

```bash
docker compose exec -T postgres \
  pg_dump -U openea -d openea -Fc \
  > openea-backup.dump
```

If you changed `POSTGRES_USER` or `POSTGRES_DB`, substitute those values.

## Protect configuration separately

Database backups do not include your `.env` file. Protect configuration and secrets separately and do not commit them to source control.

## Restore procedure

Restore into a tested empty PostgreSQL database using standard PostgreSQL tools.

For Docker installations:

1. Stop the OpenEA web and worker so no writes occur during recovery.
2. Restore the database.
3. Start the stack.
4. Run Alembic to bring the restored database to the current schema level.

```bash
docker compose exec web alembic upgrade head
```

For OpenEA Community 1.5.2, the current head is:

```text
0016_phase15
```

## Verify after restore

Check:

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
docker compose exec web alembic current
```

Then verify users, representative architecture records, relationships, audit history, metrics, and findings.
