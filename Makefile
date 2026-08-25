.PHONY: run test lint migrate
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
