# ─────────────────────────────────────────────────────────────
# Makefile for TaskFlow — Distributed Task Queue System
# ─────────────────────────────────────────────────────────────

.PHONY: help install install-dev dev \
        test test-cov test-frontend test-all \
        lint lint-backend lint-frontend type-check format \
        build build-frontend build-docker \
        deploy deploy-staging deploy-production \
        docker-up docker-down docker-prod-build docker-prod-up docker-prod-down \
        docker-prod-logs docker-prod-restart \
        monitoring-up monitoring-down \
        migrate seed seed-clean validate-env validate-env-strict \
        security-scan security-audit \
        pre-commit pre-commit-install \
        clean clean-all

# ── Help ──────────────────────────────────────────────────────
help:
	@echo "TaskFlow — Distributed Task Queue System"
	@echo ""
	@echo "Development:"
	@echo "  make install            Install production dependencies"
	@echo "  make install-dev        Install all dependencies (prod + dev)"
	@echo "  make dev                Run development server"
	@echo "  make pre-commit-install Set up pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make test               Run backend tests"
	@echo "  make test-cov           Run backend tests with coverage"
	@echo "  make test-frontend      Run frontend tests"
	@echo "  make test-all           Run all tests (backend + frontend)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint               Run all linters (backend + frontend)"
	@echo "  make lint-backend       Run Python linters (ruff + black + isort)"
	@echo "  make lint-frontend      Run ESLint on frontend"
	@echo "  make type-check         Run type checkers (mypy + tsc)"
	@echo "  make format             Auto-format all code"
	@echo "  make pre-commit         Run all pre-commit hooks"
	@echo ""
	@echo "Build:"
	@echo "  make build              Build everything (frontend + Docker)"
	@echo "  make build-frontend     Build frontend for production"
	@echo "  make build-docker       Build all Docker images"
	@echo ""
	@echo "Security:"
	@echo "  make security-scan      Run dependency vulnerability scan"
	@echo "  make security-audit     Run full security audit script"
	@echo ""
	@echo "Database:"
	@echo "  make migrate            Run Alembic migrations"
	@echo "  make seed               Seed database with demo data"
	@echo "  make seed-clean         Clear all data and re-seed"
	@echo ""
	@echo "Docker — Development:"
	@echo "  make docker-up          Start dev containers"
	@echo "  make docker-down        Stop dev containers"
	@echo ""
	@echo "Docker — Production:"
	@echo "  make docker-prod-build  Build production images"
	@echo "  make docker-prod-up     Start production stack"
	@echo "  make docker-prod-down   Stop production stack"
	@echo "  make docker-prod-logs   Tail production logs"
	@echo ""
	@echo "Monitoring:"
	@echo "  make monitoring-up      Start Prometheus + Grafana"
	@echo "  make monitoring-down    Stop monitoring stack"
	@echo ""
	@echo "Deploy:"
	@echo "  make deploy-staging     Deploy to staging environment"
	@echo "  make deploy-production  Deploy to production environment"
	@echo ""
	@echo "Utilities:"
	@echo "  make validate-env       Validate environment configuration"
	@echo "  make clean              Clean build artifacts"
	@echo "  make clean-all          Deep clean (incl. node_modules, venv)"

# ── Development ────────────────────────────────────────────────
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	cd frontend && npm ci

dev:
	python run.py

pre-commit-install:
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg

# ── Testing ────────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

test-frontend:
	cd frontend && npm test -- --watchAll=false --coverage

test-all: test test-frontend

# ── Code Quality ───────────────────────────────────────────────
lint: lint-backend lint-frontend

lint-backend:
	ruff check src tests
	black --check --line-length 120 src tests
	isort --check-only --profile black --line-length 120 src tests

lint-frontend:
	cd frontend && npx eslint src/ --max-warnings 0

type-check:
	mypy src --ignore-missing-imports
	cd frontend && npx tsc --noEmit

format:
	ruff check --fix src tests || true
	black --line-length 120 src tests
	isort --profile black --line-length 120 src tests
	cd frontend && npx eslint src/ --fix || true

pre-commit:
	pre-commit run --all-files

# ── Build ─────────────────────────────────────────────────────
build: build-frontend build-docker

build-frontend:
	cd frontend && npm ci && npm run build

build-docker:
	docker compose -f docker-compose.prod.yml build

# ── Security ──────────────────────────────────────────────────
security-scan:
	pip-audit -r requirements.txt || true
	cd frontend && npm audit --audit-level=high || true

security-audit:
	python scripts/security_audit.py

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

# ── Deploy ────────────────────────────────────────────────────
deploy-staging:
	@echo "Deploying to staging..."
	docker compose -f docker-compose.prod.yml --env-file .env.staging pull
	docker compose -f docker-compose.prod.yml --env-file .env.staging up -d
	@echo "Staging deployment complete. Running smoke tests..."
	curl -sf http://localhost:5000/health || (echo "Health check failed!" && exit 1)

deploy-production:
	@echo "WARNING: Deploying to production!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose -f docker-compose.prod.yml --env-file .env pull
	docker compose -f docker-compose.prod.yml --env-file .env up -d
	@echo "Production deployment complete."
	curl -sf http://localhost:5000/health || (echo "Health check failed!" && exit 1)

# ── Cleanup ───────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -name .coverage -delete
	rm -rf build/ dist/ *.egg-info/

clean-all: clean
	rm -rf frontend/node_modules frontend/dist
	rm -rf .venv venv
	rm -rf frontend/coverage
	docker compose down --volumes --remove-orphans 2>/dev/null || true

.DEFAULT_GOAL := help
