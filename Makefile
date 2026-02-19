.PHONY: help install dev test build deploy clean

help:
	@echo "Available commands:"
	@echo "  install    - Install all dependencies"
	@echo "  dev        - Start development environment"
	@echo "  test       - Run all tests"
	@echo "  build      - Build Docker images"
	@echo "  deploy     - Deploy to production"
	@echo "  clean      - Clean up temporary files"

install:
	poetry install
	cd frontend && npm install

dev:
	docker-compose up -d postgres redis chroma
	poetry run uvicorn src.api.main:app --reload &
	cd frontend && npm start

test:
	poetry run pytest tests/ -v --cov=src
	cd frontend && npm test

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