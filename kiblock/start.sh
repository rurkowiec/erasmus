#!/bin/bash

# Quick Start Script for KiBlock Docker

echo "=========================================="
echo "KiBlock Docker Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed."
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed."
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker is installed"
echo "✓ Docker Compose is installed"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file (you can edit it to change settings)"
else
    echo "✓ .env file already exists"
fi
echo ""

# Build and start
echo "Building Docker image..."
docker-compose build

echo ""
echo "Starting application..."
docker-compose up -d

echo ""
echo "=========================================="
echo "✓ KiBlock is now running!"
echo "=========================================="
echo ""
echo "Access the application at: http://localhost:9025"
echo ""
echo "To create an admin user, run:"
echo "  docker-compose exec web python manage.py createsuperuser"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the application:"
echo "  docker-compose down"
echo ""
echo "For more commands, see DOCKER_README.md"
echo ""
