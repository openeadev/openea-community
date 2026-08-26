#!/bin/sh
set -eu

echo "==> OpenEA Community Render startup"

echo "==> Applying database migrations"
alembic upgrade head

echo "==> Checking demo deployment state"
python scripts/reset-demo-on-deploy.py

echo "==> Starting OpenEA background worker"
python -m app.workers.metrics_worker &
WORKER_PID=$!

echo "==> Starting OpenEA Community web service"
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-10000}" &
WEB_PID=$!

shutdown() {
    echo "==> Shutting down OpenEA Community"

    kill -TERM "$WEB_PID" 2>/dev/null || true
    kill -TERM "$WORKER_PID" 2>/dev/null || true

    wait "$WEB_PID" 2>/dev/null || true
    wait "$WORKER_PID" 2>/dev/null || true
}

trap shutdown INT TERM EXIT

wait "$WEB_PID"
WEB_STATUS=$?

kill -TERM "$WORKER_PID" 2>/dev/null || true
wait "$WORKER_PID" 2>/dev/null || true

exit "$WEB_STATUS"