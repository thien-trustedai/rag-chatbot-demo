#!/bin/bash

# PDF RAG Chat Application Startup Script

set -e

echo "🚀 Starting PDF RAG Chat Application..."

# Check if .env file exists
if [ ! -f ./backend/.env ]; then
    echo "⚠️  Warning: backend/.env file not found!"
    echo "Please copy backend/.env.example to backend/.env and configure it."
    exit 1
fi

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Parse arguments
MODE=${1:-dev}

case $MODE in
    dev|development)
        echo "📦 Starting in DEVELOPMENT mode..."
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    prod|production)
        echo "📦 Starting in PRODUCTION mode..."
        docker-compose up -d --build
        echo "✅ Application started!"
        echo "   Frontend: http://localhost:3000"
        echo "   Backend:  http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo ""
        echo "Use 'docker-compose logs -f' to view logs"
        ;;
    stop)
        echo "🛑 Stopping application..."
        docker-compose down
        docker-compose -f docker-compose.dev.yml down
        echo "✅ Application stopped"
        ;;
    clean)
        echo "🧹 Cleaning up..."
        docker-compose down -v
        docker-compose -f docker-compose.dev.yml down -v
        docker system prune -f
        echo "✅ Cleanup complete"
        ;;
    *)
        echo "Usage: ./start.sh [dev|prod|stop|clean]"
        echo "  dev   - Start in development mode with hot-reload"
        echo "  prod  - Start in production mode"
        echo "  stop  - Stop all containers"
        echo "  clean - Stop and remove all containers, volumes, and images"
        exit 1
        ;;
esac