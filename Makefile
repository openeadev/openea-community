DOCS_HOST ?= 127.0.0.1
DOCS_PORT ?= 8001
DOCS_PID_FILE ?= .mkdocs.pid
DOCS_LOG_FILE ?= .mkdocs.log

.PHONY: run test lint migrate build docs docs-stop docs-status docs-build

run:
	python -m pip install -e '.[dev]'
	uvicorn app.main:app --reload

test:
	curl http://localhost:8000/health
	curl http://localhost:8000/health/ready
	pytest

lint:
	ruff check .

migrate:
	alembic upgrade head

build:
	docker compose down
	docker compose build --no-cache
	docker compose up -d
	docker compose exec web alembic current

docs:
	@set -eu; \
	command -v mkdocs >/dev/null 2>&1 || { \
		echo "MkDocs is not installed. Run: python -m pip install -r requirements-docs.txt"; \
		exit 1; \
	}; \
	if [ -f "$(DOCS_PID_FILE)" ]; then \
		pid="$$(cat "$(DOCS_PID_FILE)")"; \
		if kill -0 "$$pid" 2>/dev/null; then \
			echo "MkDocs is already running (PID $$pid) at http://$(DOCS_HOST):$(DOCS_PORT)/"; \
			exit 0; \
		fi; \
		rm -f "$(DOCS_PID_FILE)"; \
	fi; \
	echo "Starting MkDocs at http://$(DOCS_HOST):$(DOCS_PORT)/"; \
	nohup mkdocs serve --dev-addr "$(DOCS_HOST):$(DOCS_PORT)" > "$(DOCS_LOG_FILE)" 2>&1 & \
	pid=$$!; \
	echo "$$pid" > "$(DOCS_PID_FILE)"; \
	sleep 1; \
	if kill -0 "$$pid" 2>/dev/null; then \
		echo "MkDocs started in the background (PID $$pid). Log: $(DOCS_LOG_FILE)"; \
	else \
		echo "MkDocs failed to start. Check $(DOCS_LOG_FILE)"; \
		rm -f "$(DOCS_PID_FILE)"; \
		exit 1; \
	fi

docs-stop:
	@set -eu; \
	if [ ! -f "$(DOCS_PID_FILE)" ]; then \
		echo "MkDocs is not running (no $(DOCS_PID_FILE) file)."; \
		exit 0; \
	fi; \
	pid="$$(cat "$(DOCS_PID_FILE)")"; \
	if kill -0 "$$pid" 2>/dev/null; then \
		kill "$$pid"; \
		echo "Stopped MkDocs (PID $$pid)."; \
	else \
		echo "Removed stale MkDocs PID file (PID $$pid was not running)."; \
	fi; \
	rm -f "$(DOCS_PID_FILE)"

docs-status:
	@if [ -f "$(DOCS_PID_FILE)" ] && kill -0 "$$(cat "$(DOCS_PID_FILE)")" 2>/dev/null; then \
		echo "MkDocs is running (PID $$(cat "$(DOCS_PID_FILE)")) at http://$(DOCS_HOST):$(DOCS_PORT)/"; \
	else \
		echo "MkDocs is not running."; \
	fi

docs-build:
	@set -eu; \
	command -v mkdocs >/dev/null 2>&1 || { \
		echo "MkDocs is not installed. Run: python -m pip install -r requirements-docs.txt"; \
		exit 1; \
	}; \
	mkdocs build --strict
