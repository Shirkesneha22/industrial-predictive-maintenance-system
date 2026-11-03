.PHONY: help setup setup-starter test validate reproduce up down

PYTHON ?= python

help:
	@echo "Available commands:"
	@echo "  make setup         - Full end-to-end setup (migrate + generate 90-day full dataset + export + validate)"
	@echo "  make setup-starter - Starter setup (migrate + generate 10-day starter dataset + export + validate)"
	@echo "  make test          - Run automated backend test suite (requires running PostgreSQL)"
	@echo "  make validate      - Run relational and domain integrity validations"
	@echo "  make reproduce     - Run deterministic seed-based reproducibility check"
	@echo "  make up            - Launch PostgreSQL, Backend, and Frontend via Docker Compose"
	@echo "  make down          - Stop and clean up Docker Compose containers"

setup:
	alembic -c backend/alembic.ini upgrade head
	$(PYTHON) -m backend.generators.cli master-data
	$(PYTHON) -m backend.generators.cli failures
	$(PYTHON) -m backend.generators.cli telemetry --scale full
	$(PYTHON) -m backend.generators.cli export
	$(PYTHON) -m backend.generators.cli validate

setup-starter:
	alembic -c backend/alembic.ini upgrade head
	$(PYTHON) -m backend.generators.cli master-data
	$(PYTHON) -m backend.generators.cli failures
	$(PYTHON) -m backend.generators.cli telemetry --scale starter
	$(PYTHON) -m backend.generators.cli export
	$(PYTHON) -m backend.generators.cli validate

test:
	pytest backend/tests

validate:
	$(PYTHON) -m backend.generators.cli validate

reproduce:
	$(PYTHON) -m backend.generators.cli reproduce

up:
	docker compose up -d

down:
	docker compose down
