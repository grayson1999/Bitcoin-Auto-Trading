.PHONY: dev dev-down dev-logs dev-backend dev-frontend test test-backend test-frontend lint lint-fix build db-migrate db-revision clean

# Docker Compose
dev:
	docker-compose up -d

dev-down:
	docker-compose down

dev-logs:
	docker-compose logs -f

# Backend (local development)
dev-backend:
	cd backend && uv run uvicorn src.main:app --reload --port 8000

# Frontend (local development)
dev-frontend:
	cd frontend && npm run dev

# Testing
test:
	cd backend && uv run pytest
	cd frontend && npm test

test-backend:
	cd backend && uv run pytest

test-frontend:
	cd frontend && npm test

# Linting
lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint

lint-fix:
	cd backend && uv run ruff check --fix . && uv run ruff format .
	cd frontend && npm run lint -- --fix

# Build
build:
	docker-compose build

# Database migrations
db-migrate:
	cd backend && uv run alembic upgrade head

db-revision:
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

# Clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
