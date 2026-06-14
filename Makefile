.PHONY: dev-db dev-db-down dev-db-logs dev-backend dev-frontend test test-backend test-frontend lint lint-fix db-migrate db-revision scan-secrets clean

# PostgreSQL (Docker)
dev-db:
	docker compose up -d

dev-db-down:
	docker compose down

dev-db-logs:
	docker compose logs -f db

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

# Database migrations
db-migrate:
	cd backend && uv run alembic upgrade head

db-revision:
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

# Secret scanning (gitleaks 설치 필요: https://github.com/gitleaks/gitleaks)
scan-secrets:
	@command -v gitleaks >/dev/null 2>&1 || { echo "gitleaks 미설치 - 'brew install gitleaks' 또는 릴리스 바이너리 설치 필요"; exit 1; }
	gitleaks detect --config .gitleaks.toml --no-banner --redact

# Clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
