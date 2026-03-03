.PHONY: help build up down restart logs shell createsuperuser migrate clean

help:
	@echo "KiBlock Docker Commands:"
	@echo "  make build          - Build the Docker image"
	@echo "  make up             - Start the application"
	@echo "  make down           - Stop the application"
	@echo "  make restart        - Restart the application"
	@echo "  make logs           - View application logs"
	@echo "  make shell          - Access container shell"
	@echo "  make createsuperuser - Create admin user"
	@echo "  make migrate        - Run database migrations"
	@echo "  make clean          - Remove containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Application started at http://localhost:9025"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

shell:
	docker-compose exec web bash

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

migrate:
	docker-compose exec web python manage.py migrate

clean:
	docker-compose down -v
	@echo "Warning: This will remove the database. Back up data/ first!"
