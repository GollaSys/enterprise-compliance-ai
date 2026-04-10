.PHONY: help install dev test build deploy clean demo demo-stop smoke

help:
	@echo "Available commands:"
	@echo "  install    - Install all dependencies"
	@echo "  dev        - Start development environment"
	@echo "  demo       - Start all services + open demo instructions"
	@echo "  demo-stop  - Stop all demo services"
	@echo "  smoke      - Run demo smoke test (real LLM calls, ~30s)"
	@echo "  test       - Run all tests"
	@echo "  build      - Build Docker images"
	@echo "  deploy     - Deploy to production"
	@echo "  clean      - Clean up temporary files"

install:
	pip install -r requirements-minimal.txt
	cd frontend && npm install --legacy-peer-deps

dev:
	docker-compose up -d postgres redis chroma
	source venv/bin/activate && uvicorn src.api.main_simple:app --port 8001 --reload &
	cd frontend && REACT_APP_API_URL=http://localhost:8001 npm start

# ── Demo commands ──────────────────────────────────────────────────────────

demo:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║       Enterprise Compliance AI — Agent Demo          ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Starting services..."
	docker-compose up -d postgres redis chroma langfuse-db langfuse
	@echo ""
	@echo "Starting backend on :8001..."
	@source venv/bin/activate && uvicorn src.api.main_simple:app --port 8001 --reload &
	@sleep 2
	@echo ""
	@echo "Starting frontend on :3000..."
	@cd frontend && REACT_APP_API_URL=http://localhost:8001 npm start &
	@sleep 3
	@echo ""
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║  Demo ready!                                         ║"
	@echo "║                                                      ║"
	@echo "║  1. Frontend:  http://localhost:3000/demo            ║"
	@echo "║  2. Backend:   http://localhost:8001/docs            ║"
	@echo "║  3. Langfuse:  http://localhost:3001                 ║"
	@echo "║                                                      ║"
	@echo "║  Click 'Run with sample GDPR doc' to start          ║"
	@echo "║  Run twice to see mem0 long-term memory in action   ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""

demo-stop:
	@echo "Stopping demo services..."
	docker-compose stop langfuse langfuse-db
	@pkill -f "uvicorn src.api.main_simple" || true
	@pkill -f "react-scripts start" || true
	@echo "Demo stopped."

smoke:
	@echo "Running smoke test (real LLM calls)..."
	@source venv/bin/activate && python scripts/demo_smoke_test.py

# ── Standard commands ──────────────────────────────────────────────────────

test:
	source venv/bin/activate && python -m pytest tests/ -v

build:
	docker-compose build

deploy:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -f data/checkpoints.db
