.PHONY: run test lint migrate
run:
	python -m pip install -e '.[dev]'
	uvicorn app.main:app --reload

test:
	pip install -e '.[dev]'
	ruff check .
	python -m compileall -q app scripts
	pytest -q

lint:
	ruff check .

migrate:
	alembic upgrade head

build:
	docker compose down
	docker compose build --no-cache
	docker compose up -d
	docker compose exec web alembic current
