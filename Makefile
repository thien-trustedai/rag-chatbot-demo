.PHONY: help build up down logs clean dev dev-up dev-down dev-logs

help:
	@echo "Available commands:"
	@echo "  make build       - Build Docker images for production"
	@echo "  make up          - Start production containers"
	@echo "  make down        - Stop and remove containers"
	@echo "  make logs        - View container logs"
	@echo "  make clean       - Clean up volumes and images"
	@echo "  make dev         - Start development environment"
	@echo "  make dev-build   - Build development images"
	@echo "  make dev-up      - Start development containers"
	@echo "  make dev-down    - Stop development containers"
	@echo "  make dev-logs    - View development logs"

# Production commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

# Development commands
dev: dev-build dev-up

dev-build:
	docker-compose -f docker-compose.dev.yml build

dev-up:
	docker-compose -f docker-compose.dev.yml up

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Utility commands
shell-backend:
	docker exec -it pdf-rag-backend-dev /bin/bash

shell-frontend:
	docker exec -it pdf-rag-frontend-dev /bin/sh

restart-backend:
	docker-compose -f docker-compose.dev.yml restart backend

restart-frontend:
	docker-compose -f docker-compose.dev.yml restart frontend