SHELL := /bin/bash

.PHONY: help setup setup-backend setup-frontend lint lint-backend lint-frontend type-check test test-backend test-frontend ci clean

help:
	@echo "Available targets:"
	@echo "  setup           Install backend and frontend dependencies"
	@echo "  setup-backend   pip install backend requirements"
	@echo "  setup-frontend  npm install frontend dependencies"
	@echo "  lint            Run backend + frontend lint"
	@echo "  type-check      Run frontend type-check"
	@echo "  test            Run backend + frontend tests"
	@echo "  ci              Run local CI-equivalent checks"

setup: setup-backend setup-frontend

setup-backend:
	python -m pip install -r backend/requirements.txt
	python -m pip install ruff

setup-frontend:
	cd frontend && npm install

lint: lint-backend lint-frontend

lint-backend:
	cd backend && ruff check app tests

lint-frontend:
	cd frontend && npm run lint

type-check:
	cd frontend && npm run type-check

test: test-backend test-frontend

test-backend:
	cd backend && pytest -q

test-frontend:
	cd frontend && npm run test:unit

ci: setup lint type-check test

clean:
	rm -f backend/app.db
	rm -rf backend/.pytest_cache frontend/node_modules frontend/.vitest
