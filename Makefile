# Makefile for Lithium Bot Project

.PHONY: up down restart init test lint logs ps

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

init:
	docker-compose exec api alembic upgrade head
	docker-compose exec api python lithium_core/scripts/seed.py
	@echo "Migrations and seeding completed."

test:
	docker-compose exec api pytest tests/unit
	docker-compose exec api pytest tests/integration
	@echo "Smoke tests (healthchecks):"
	docker-compose ps --format "table {{.Name}}\t{{.Status}}"

lint:
	docker-compose exec api flake8 apps lithium_core
	docker-compose exec api black --check apps lithium_core

logs:
	docker-compose logs -f

ps:
	docker-compose ps
