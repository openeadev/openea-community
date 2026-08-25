# Backup and Restore

PostgreSQL is OpenEA's Community authoritative persistent store. Back it up before upgrades and before large imports.

## Docker backup

```bash
docker compose exec -T postgres pg_dump -U openea -d openea -Fc > openea-backup.dump
```

If custom `POSTGRES_USER` or `POSTGRES_DB` values are configured, substitute those values.

## Restore

Restore into a tested empty database using PostgreSQL tools. For a Docker installation, stop the web and worker before restoring so no writes occur during recovery. After restore, start the stack and run `docker compose exec web alembic upgrade head` to ensure the restored database is at the current schema revision.

Backups should include the `.env` configuration separately, but secrets should be protected and never committed to source control.
