.DEFAULT_GOAL := help
.PHONY: help install dev seed sync agent test cov load check lint format hooks docker-build docker-up docker-down clean

PYTHON := poetry run python

help:
	@echo "Hardy"
	@echo ""
	@echo "  make install      poetry install, into an in-project .venv"
	@echo "  make install-pip  same thing without poetry, for a judge in a hurry"
	@echo "  make dev          run on http://127.0.0.1:8000 with hot reload"
	@echo "  make seed         seed the catalog through Mesh, idempotent on re-run"
	@echo "  make sync         embed every product and upsert it into Qdrant"
	@echo "  make agent        run the LangGraph agent end to end"
	@echo "  make test         run the test suite"
	@echo "  make cov          run the test suite with a coverage report"
	@echo "  make load         drive load at a running app with Locust on :8089"
	@echo "  make check        run the four checks CI runs, including a live Mesh call"
	@echo "  make lint         ruff check"
	@echo "  make format       ruff format"
	@echo "  make hooks        install the pre-commit hooks"
	@echo "  make docker-up    run the app and a Qdrant server in containers"
	@echo "  make clean        remove caches, the database and the local vector store"

install:
	poetry install

install-pip:
	python3 -m venv .venv
	.venv/bin/pip install --quiet --upgrade pip
	.venv/bin/pip install --quiet -r requirements.txt -r requirements-dev.txt

dev:
	$(PYTHON) -m hypercorn src.main:app --bind 127.0.0.1:8000 --reload

seed:
	$(PYTHON) -m scripts.seed_catalog

sync:
	$(PYTHON) -m scripts.sync_vectors

agent:
	$(PYTHON) -m scripts.run_agent

test:
	$(PYTHON) -m pytest

cov:
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing

load:
	docker run --rm -it -p 8089:8089 -v "$(PWD)":/mnt/locust locustio/locust \
		-f /mnt/locust/locustfile.py --host http://host.docker.internal:8000

check:
	$(PYTHON) -m scripts.check

lint:
	$(PYTHON) -m ruff check src scripts tests

format:
	$(PYTHON) -m ruff format src scripts tests

hooks:
	$(PYTHON) -m pre_commit install
	$(PYTHON) -m pre_commit install --hook-type commit-msg

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	rm -rf .ruff_cache .pytest_cache qdrant_data hardy.db
	find . -name __pycache__ -not -path "./.venv/*" -type d -exec rm -rf {} +
