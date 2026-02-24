# ─────────────────────────────────────────────────────────────
# Makefile for TaskFlow — Distributed Task Queue System
# ─────────────────────────────────────────────────────────────

.PHONY: help install dev test test-cov test-frontend lint format clean \
        docker-up docker-down docker-prod-up docker-prod-down docker-prod-build \
        monitoring-up monitoring-down \
        migrate seed validate-env

# ── Help ──────────────────────────────────────────────────────
help:
	@echo "TaskFlow - Distributed Task Queue System"
	@echo ""
	@echo "Development:"
	@echo "  make install          Install Python dependencies"
	@echo "  make dev              Run development server"
	@echo "  make test             Run backend tests"
	@echo "  make test-cov         Run backend tests with coverage"
	@echo "  make test-frontend    Run frontend tests"
	@echo "  make lint             Run linters"
	@echo "  make format           Format code"
	@echo "  make clean            Clean build artifacts"
	@echo ""
	@echo "Database:"
	@echo "  make migrate          Run Alembic migrations"
	@echo "  make seed             Seed database with demo data"
	@echo "  make seed-clean       Clear all data and re-seed"
	@echo ""
	@echo "Docker — Development:"
	@echo "  make docker-up        Start dev containers"
	@echo "  make docker-down      Stop dev containers"
	@echo ""
	@echo "Docker — Production:"
	@echo "  make docker-prod-build  Build production images"
	@echo "  make docker-prod-up     Start production stack"
	@echo "  make docker-prod-down   Stop production stack"
	@echo "  make docker-prod-logs   Tail production logs"
	@echo ""
	@echo "Monitoring:"
	@echo "  make monitoring-up    Start Prometheus + Grafana"
	@echo "  make monitoring-down  Stop monitoring stack"
	@echo ""
	@echo "Utilities:"
	@echo "  make validate-env     Validate environment configuration"

# ── Development ────────────────────────────────────────────────
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	python run.py

# ── Testing ────────────────────────────────────────────────────
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-frontend:
	cd frontend && npm test -- --watchAll=false

# ── Code Quality ───────────────────────────────────────────────
lint:
	flake8 src tests
	mypy src
	black --check src tests

format:
	black src tests
	isort src tests

# ── Database ───────────────────────────────────────────────────
migrate:
	alembic upgrade head

seed:
	python scripts/seed_data.py

seed-clean:
	python scripts/seed_data.py --clear

# ── Environment Validation ────────────────────────────────────
validate-env:
	python scripts/validate_env.py

validate-env-strict:
	python scripts/validate_env.py --strict

# ── Docker — Development ──────────────────────────────────────
docker-up:
	docker compose up -d

docker-down:
	docker compose down

# ── Docker — Production ──────────────────────────────────────
docker-prod-build:
	docker compose -f docker-compose.prod.yml build

docker-prod-up:
	docker compose -f docker-compose.prod.yml --env-file .env up -d

docker-prod-down:
	docker compose -f docker-compose.prod.yml down

docker-prod-logs:
	docker compose -f docker-compose.prod.yml logs -f --tail=100

docker-prod-restart:
	docker compose -f docker-compose.prod.yml restart

# ── Monitoring Stack ──────────────────────────────────────────
monitoring-up:
	docker compose -f deployment/docker/docker-compose.monitoring.yml --env-file .env up -d

monitoring-down:
	docker compose -f deployment/docker/docker-compose.monitoring.yml down

# ── Cleanup ───────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -name .coverage -delete
	rm -rf build/ dist/ *.egg-info/

.DEFAULT_GOAL := help
