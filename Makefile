# Makefile for TaskFlow

.PHONY: help install dev test lint format clean docker-up docker-down migrate

help:
	@echo "TaskFlow - Distributed Task Queue System"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make migrate      - Run database migrations"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	python run.py

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html

lint:
	flake8 src tests
	mypy src
	black --check src tests

format:
	black src tests
	isort src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -name .coverage -delete
	rm -rf build/ dist/ *.egg-info/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	alembic upgrade head

.DEFAULT_GOAL := help
