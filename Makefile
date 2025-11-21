.PHONY: help install run stop test clean logs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*##"; printf "\033[36m\033[0m"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

run: ## Start all services with Docker Compose
	docker-compose up -d
	@echo "Services started!"
	@echo "UI: http://localhost:8501"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Flower: http://localhost:5555"

stop: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

build: ## Build Docker images
	docker-compose build

test: ## Run tests
	pytest tests/ -v

test-coverage: ## Run tests with coverage
	pytest tests/ --cov=app --cov-report=html --cov-report=term

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API logs
	docker-compose logs -f api

logs-worker: ## Show worker logs
	docker-compose logs -f worker

logs-ui: ## Show UI logs
	docker-compose logs -f ui

clean: ## Clean up containers, volumes, and cache
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

shell-api: ## Open shell in API container
	docker-compose exec api /bin/bash

shell-worker: ## Open shell in worker container
	docker-compose exec worker /bin/bash

shell-ui: ## Open shell in UI container
	docker-compose exec ui /bin/bash

redis-cli: ## Connect to Redis CLI
	docker-compose exec redis redis-cli

format: ## Format code with black
	black app/ tests/ ui/

lint: ## Lint code with ruff
	ruff check app/ tests/ ui/

ui-local: ## Run UI locally (for development)
	streamlit run ui/app.py --server.port=8501

env: ## Copy .env.example to .env
	cp .env.example .env
	@echo "Created .env file. Please edit it with your configuration."
