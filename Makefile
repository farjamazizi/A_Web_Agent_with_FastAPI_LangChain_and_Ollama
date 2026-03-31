PYTHON ?= python
PIP ?= pip
NPM ?= npm
FRONTEND_DIR := app/frontend

.PHONY: help install install-dev test backend frontend-install frontend-dev frontend-build check clean

help:
	@echo "Available targets:"
	@echo "  install           Install Python package"
	@echo "  install-dev       Install Python package with dev dependencies"
	@echo "  test              Run backend tests"
	@echo "  backend           Start FastAPI backend"
	@echo "  frontend-install  Install frontend dependencies"
	@echo "  frontend-dev      Start React frontend"
	@echo "  frontend-build    Build React frontend"
	@echo "  check             Run compile checks, tests, and frontend build"
	@echo "  clean             Remove common generated files"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e '.[dev]'

test:
	$(PYTHON) -m pytest -q tests/test_api.py tests/test_schemas.py

backend:
	uvicorn app.backend.main:app --reload

frontend-install:
	cd $(FRONTEND_DIR) && $(NPM) install

frontend-dev:
	cd $(FRONTEND_DIR) && $(NPM) run dev

frontend-build:
	cd $(FRONTEND_DIR) && $(NPM) run build

check:
	$(PYTHON) -m compileall src app/backend tests
	$(MAKE) test
	$(MAKE) frontend-build

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf $(FRONTEND_DIR)/dist
