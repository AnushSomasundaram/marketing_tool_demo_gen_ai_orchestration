.PHONY: install migrate dev test lint format

install:
	python3.12 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

migrate:
	. .venv/bin/activate && alembic upgrade head

dev:
	. .venv/bin/activate && uvicorn app.main:app --reload

test:
	. .venv/bin/activate && pytest -q

lint:
	. .venv/bin/activate && ruff check .

format:
	. .venv/bin/activate && ruff format . && ruff check --fix .
