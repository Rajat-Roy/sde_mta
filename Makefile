.PHONY: help build up down restart logs shell migrate test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker compose build

up: ## Start all services
	docker compose up

up-d: ## Start all services in detached mode
	docker compose up -d

down: ## Stop all services
	docker compose down

clean-start: ## Clean start (remove volumes and rebuild)
	docker compose down -v
	docker compose build
	docker compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "All services started!"

restart: ## Restart all services
	docker compose restart

logs: ## View logs from all services
	docker compose logs -f

logs-web: ## View Django logs
	docker compose logs -f web

logs-celery: ## View Celery logs
	docker compose logs -f celery

logs-db: ## View PostgreSQL logs
	docker compose logs -f db

shell: ## Open Django shell
	docker compose exec web python manage.py shell

bash: ## Open bash in web container
	docker compose exec web bash

migrate: ## Run database migrations
	docker compose exec web python manage.py migrate

makemigrations: ## Create new migrations
	docker compose exec web python manage.py makemigrations

createsuperuser: ## Create Django superuser
	docker compose exec web python manage.py createsuperuser

collectstatic: ## Collect static files
	docker compose exec web python manage.py collectstatic --noinput

test: ## Run tests
	docker compose exec web python manage.py test

db-shell: ## Access PostgreSQL shell
	docker compose exec db psql -U mkt_user -d mkt_db

redis-cli: ## Access Redis CLI
	docker compose exec redis redis-cli

clean: ## Stop and remove all containers, volumes, and images
	docker compose down -v --rmi all

reset-db: ## Reset database (WARNING: deletes all data)
	docker compose down -v
	docker compose up -d db
	sleep 5
	docker compose exec web python manage.py migrate

dev: ## Start in development mode with hot reload
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

remote-up: ## Start with remote PostgreSQL database
	docker compose -f docker-compose.remote-db.yml up

remote-up-d: ## Start with remote DB in detached mode
	docker compose -f docker-compose.remote-db.yml up -d

remote-down: ## Stop services using remote DB
	docker compose -f docker-compose.remote-db.yml down

remote-build: ## Build images for remote DB setup
	docker compose -f docker-compose.remote-db.yml build

prod-build: ## Build for production
	docker compose -f docker-compose.yml build

ps: ## Show running containers
	docker compose ps

stats: ## Show container resource usage
	docker stats
