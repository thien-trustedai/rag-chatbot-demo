# Docker Setup for PDF RAG Chat Application

This application uses Docker Compose to orchestrate the frontend (Next.js) and backend (FastAPI) services.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose V2
- `.env` file in the backend directory with Azure OpenAI credentials

## Quick Start

### Development Mode (with hot-reload)

```bash
# Start both services in development mode
make dev

# Or manually:
docker-compose -f docker-compose.dev.yml up
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Production Mode

```bash
# Build and start services
make build
make up

# Or in one command:
docker-compose up -d --build
```

## Available Commands

### Using Make (Recommended)

```bash
make help         # Show all available commands
make dev          # Start development environment
make dev-down     # Stop development containers
make dev-logs     # View development logs
make build        # Build production images
make up           # Start production containers
make down         # Stop containers
make logs         # View logs
make clean        # Clean up volumes and images
```

### Using Docker Compose Directly

```bash
# Development
docker-compose -f docker-compose.dev.yml up     # Start with logs
docker-compose -f docker-compose.dev.yml up -d  # Start in background
docker-compose -f docker-compose.dev.yml down   # Stop containers
docker-compose -f docker-compose.dev.yml logs -f # View logs

# Production
docker-compose up -d --build  # Build and start
docker-compose down           # Stop containers
docker-compose logs -f        # View logs
```

## Architecture

### Services

1. **Backend (FastAPI)**
   - Port: 8000
   - Features: PDF extraction, ChromaDB indexing, RAG queries
   - Volumes: uploads, extractions, chroma_db

2. **Frontend (Next.js)**
   - Port: 3000
   - Features: PDF viewer, chat interface, real-time updates
   - Connects to backend via internal Docker network

### Volumes

- `uploads/`: Stores uploaded PDF files
- `extractions/`: Stores extracted content and metadata
- `chroma_db/`: Vector database storage

### Networks

- `pdf-rag-network`: Internal bridge network for service communication

## Environment Variables

### Backend (.env file required)

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01

# Embedding Configuration
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_EMBEDDING_API_KEY=your-api-key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
```

### Frontend

Environment variables are set in docker-compose files:
- `NEXT_PUBLIC_API_BASE_URL`: Backend API URL

## Troubleshooting

### Container Issues

```bash
# Check container status
docker ps

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# Restart a service
docker-compose restart backend
docker-compose restart frontend

# Access container shell
docker exec -it pdf-rag-backend-dev /bin/bash
docker exec -it pdf-rag-frontend-dev /bin/sh
```

### Common Problems

1. **Port already in use**: Stop local services or change ports in docker-compose
2. **Volume permissions**: Ensure Docker has permissions to create/modify volumes
3. **Memory issues**: Increase Docker Desktop memory allocation
4. **Build failures**: Clear Docker cache with `docker system prune -a`

### Cleanup

```bash
# Stop and remove all containers, networks, volumes
make clean

# Or manually:
docker-compose down -v
docker system prune -a
```

## Development Workflow

1. Make changes to code (hot-reload enabled)
2. Backend changes reflect immediately
3. Frontend changes trigger Next.js fast refresh
4. Use `make dev-logs` to monitor both services

## Production Deployment

1. Update environment variables for production
2. Build optimized images: `make build`
3. Start services: `make up`
4. Monitor: `make logs`

## Health Checks

Both services include health checks:
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3000` (Next.js default)

Docker will automatically restart unhealthy containers.