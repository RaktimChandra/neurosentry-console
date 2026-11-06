# NeuroSentry Clinical Console — common developer commands.

.PHONY: help dev dev-backend dev-frontend install test build docker-build docker-up docker-down clean

help:
	@echo "NeuroSentry Clinical Console — available targets"
	@echo ""
	@echo "  make install         Install backend + frontend dependencies"
	@echo "  make dev-backend     Run FastAPI with auto-reload on :8000"
	@echo "  make dev-frontend    Run Vite dev server on :5173 (proxies to :8000)"
	@echo "  make test            Run backend pytest suite"
	@echo "  make build           Build production frontend bundle"
	@echo "  make docker-build    Build the production Docker image"
	@echo "  make docker-up       docker-compose up --build -d"
	@echo "  make docker-down     docker-compose down"
	@echo "  make clean           Remove build artefacts and caches"

install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && . .venv/bin/activate && python -m pytest tests/ -v

build:
	cd frontend && npm run build

docker-build:
	docker build -t neurosentry-console:local .

docker-up:
	docker-compose up --build -d
	@echo "Open http://localhost:8000"

docker-down:
	docker-compose down

clean:
	rm -rf backend/.pytest_cache backend/**/__pycache__
	rm -rf frontend/dist frontend/node_modules/.vite
	rm -f frontend/*.tsbuildinfo
