PYTHON ?= python
PIP ?= $(PYTHON) -m pip
FRONTEND_DIR := app/frontend

.PHONY: install install-frontend backend frontend test

install:
	$(PIP) install -e '.[dev]'

install-frontend:
	cd $(FRONTEND_DIR) && npm install

backend:
	$(PYTHON) -m uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd $(FRONTEND_DIR) && npm run dev

test:
	$(PYTHON) -m pytest -q
