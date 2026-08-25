#!/bin/sh
set -eu

echo "==> OpenEA Community Render startup"

echo "==> Applying database migrations"
alembic upgrade head

echo "==> Checking demo deployment state"
python scripts/reset-demo-on-deploy.py

echo "==> Starting OpenEA Community"
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-10000}"