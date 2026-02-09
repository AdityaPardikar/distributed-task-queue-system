# Docker & Deployment Guide

## Table of Contents

- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- Git

### Start Local Development

```bash
# Clone the repository
git clone <repository-url>
cd distributed-task-queue-system

# Create environment file
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

Services will be available at:

- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Local Development

### Docker Compose Services

The `docker-compose.yml` file starts:

- **PostgreSQL (postgres)**: Database server
- **Redis (redis)**: Cache server
- **Backend**: FastAPI application
- **Frontend**: React application

### Development Workflow

```bash
# View running containers
docker-compose ps

# Stop all services
docker-compose down

# Stop services and remove volumes
docker-compose down -v

# View backend logs
docker-compose logs backend

# View frontend logs
docker-compose logs frontend

# Rebuild images
docker-compose build

# Run database migrations in container
docker-compose exec backend python -m alembic upgrade head

# Access backend shell
docker-compose exec backend python

# Access frontend shell
docker-compose exec frontend sh
```

### Making Code Changes

Changes to local files are automatically reflected in containers thanks to volume mounts:

- Backend: `./src` → `/app/src`
- Frontend: `./frontend/src` → `/app/src`

No container restart needed for most changes. For new dependencies:

```bash
# Backend: Update requirements.txt, then rebuild
docker-compose build backend
docker-compose up -d backend

# Frontend: Update package.json, then rebuild
docker-compose build frontend
docker-compose up -d frontend
```

## Production Deployment

### Environment Setup

Create `.env.production` file with production values:

```env
# Database
DB_USER=dtqs_prod
DB_PASSWORD=<secure-password>
DB_NAME=dtqs_production

# Backend
FLASK_ENV=production
SECRET_KEY=<generate-with-secrets>
REDIS_PASSWORD=<secure-password>

# Frontend
VITE_API_URL=https://api.yourdomain.com

# Versions
BACKEND_VERSION=1.0.0
FRONTEND_VERSION=1.0.0
```

### Build and Deploy

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh production 1.0.0

# Or manually:
docker-compose -f docker-compose.prod.yml up -d
```

### Docker Image Management

```bash
# Build images with version tags
docker build -t dtqs-backend:1.0.0 -f Dockerfile.backend .
docker build -t dtqs-frontend:1.0.0 -f Dockerfile.frontend .

# Tag for registry
docker tag dtqs-backend:1.0.0 registry.example.com/dtqs-backend:1.0.0
docker tag dtqs-frontend:1.0.0 registry.example.com/dtqs-frontend:1.0.0

# Push to registry
docker push registry.example.com/dtqs-backend:1.0.0
docker push registry.example.com/dtqs-frontend:1.0.0
```

## Environment Configuration

### Common Variables

```env
# Flask/API Configuration
FLASK_ENV=production|development
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@host:5432/database
DB_POOL_SIZE=20

# Redis Cache
REDIS_URL=redis://:password@host:6379/0
REDIS_PASSWORD=password

# Security
SECRET_KEY=<generate-new-secret>
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Frontend
VITE_API_URL=http://localhost:5000

# File Storage
STORAGE_TYPE=local|s3
S3_BUCKET=bucket-name
AWS_ACCESS_KEY_ID=key
AWS_SECRET_ACCESS_KEY=secret

# Logging
LOG_LEVEL=INFO|DEBUG
LOG_FORMAT=json|text

# Features
ENABLE_ANALYTICS=true
ENABLE_NOTIFICATIONS=true
WORKER_DEAD_TIMEOUT_SECONDS=300
```

## Health Checks

### Available Endpoints

#### GET /health

Basic health check - always returns 200 if service is running

```bash
curl http://localhost:5000/health
# Response: {"status": "healthy", "version": "1.0.0", "timestamp": "2024-02-09T..."}
```

#### GET /ready

Readiness check - verifies all dependencies are available

```bash
curl http://localhost:5000/ready
# Response: {"status": "ready", "version": "1.0.0", "timestamp": "2024-02-09T..."}
```

#### GET /info

Application information

```bash
curl http://localhost:5000/info
# Response: {"name": "DTQS", "version": "1.0.0", "environment": "production", "debug": false}
```

#### GET /workers/status

Worker health status

```bash
curl http://localhost:5000/workers/status
# Response: {"status": "healthy", "total_workers": 5, "active_workers": 5, "stale_workers": 0}
```

### Docker Health Checks

Services include automatic health checks:

```bash
# Check service health
docker-compose ps

# View health status in logs
docker-compose logs postgres
docker-compose logs redis
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Rebuild image
docker-compose build <service-name>

# Full reset
docker-compose down -v
docker system prune -a
docker-compose up -d
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose exec postgres psql -U postgres -d postgres -c "SELECT 1"

# Check database exists
docker-compose exec postgres psql -U postgres -l

# Run migrations
docker-compose exec backend python -m alembic upgrade head
```

### Redis Connection Failed

```bash
# Check Redis is running and accessible
docker-compose exec redis redis-cli ping

# Check credentials (production)
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping
```

### Port Already in Use

```bash
# Change port in docker-compose.yml or .env
# Or kill process using the port
# Linux: sudo fuser -k 5000/tcp
# macOS: lsof -ti:5000 | xargs kill -9
# Windows: netstat -ano | findstr :5000
```

### Performance Issues

```bash
# Check Docker resource usage
docker stats

# Increase memory allocation in Docker Desktop settings
# Linux: Check disk space and system resources
```

### Migration Issues

```bash
# Check migration status
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Downgrade if needed
docker-compose exec backend alembic downgrade <revision>
```

## Monitoring and Logging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail 100 backend

# With timestamps
docker-compose logs -f -t backend
```

### Monitor Resources

```bash
# Real-time resource usage
docker stats

# Inspect container details
docker inspect <container-id>
```

## Security Considerations

1. **Secrets Management**: Never commit `.env` files with secrets
2. **Database**: Change default PostgreSQL password
3. **Redis**: Set authentication password in production
4. **API Key Rotation**: Regularly rotate SECRET_KEY
5. **CORS**: Restrict to specific domains in production
6. **HTTPS**: Use reverse proxy (nginx) for SSL in production
7. **Database Backups**: Implement regular backup strategy
8. **Network**: Use Docker networks, keep services internal
9. **Image Scanning**: Scan Docker images for vulnerabilities
10. **Updates**: Keep base images and dependencies updated

## Backup and Recovery

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres dtqs > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres dtqs < backup.sql
```

### Data Volume Backup

```bash
# Backup volume
docker run --rm -v dtqs_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/db-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v dtqs_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/db-backup.tar.gz -C /data
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Redis Docker Hub](https://hub.docker.com/_/redis)
