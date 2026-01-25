# Docker Setup & Usage Guide

Quick reference for Docker commands and configurations.

## Quick Start

### Development Stack (PostgreSQL + Redis only)

```bash
docker-compose -f deployment/docker/docker-compose.dev.yml up -d
```

### Full Stack (with API, Worker, Prometheus, Grafana)

```bash
docker-compose -f deployment/docker/docker-compose.prod.yml up -d
```

### Stop All Services

```bash
docker-compose -f deployment/docker/docker-compose.dev.yml down
# or
docker-compose -f deployment/docker/docker-compose.prod.yml down
```

## Available Docker Compose Files

| File                    | Location           | Purpose           | Services                                            |
| ----------------------- | ------------------ | ----------------- | --------------------------------------------------- |
| docker-compose.dev.yml  | deployment/docker/ | Local development | PostgreSQL, Redis                                   |
| docker-compose.prod.yml | deployment/docker/ | Production        | API, Worker, PostgreSQL, Redis, Prometheus, Grafana |

## Common Commands

### View Logs

```bash
# All services
docker-compose -f deployment/docker/docker-compose.dev.yml logs

# Specific service
docker-compose -f deployment/docker/docker-compose.dev.yml logs postgres
docker-compose -f deployment/docker/docker-compose.dev.yml logs redis

# Follow logs (tail -f)
docker-compose -f deployment/docker/docker-compose.dev.yml logs -f api
```

### Stop/Start Services

```bash
# Stop all
docker-compose -f deployment/docker/docker-compose.dev.yml stop

# Start all (if stopped)
docker-compose -f deployment/docker/docker-compose.dev.yml start

# Restart specific service
docker-compose -f deployment/docker/docker-compose.dev.yml restart postgres
```

### Execute Commands in Container

```bash
# Run command in API container
docker-compose -f deployment/docker/docker-compose.dev.yml exec api bash

# Run database migrations
docker-compose -f deployment/docker/docker-compose.dev.yml exec api alembic upgrade head

# Run tests
docker-compose -f deployment/docker/docker-compose.dev.yml exec api pytest
```

### View Running Containers

```bash
docker ps
docker-compose -f deployment/docker/docker-compose.dev.yml ps
```

## Health Checks

### Test Database Connection

```bash
# From host
psql -h localhost -U taskflow -d taskqueue -c "SELECT 1;"

# Or in container
docker-compose -f deployment/docker/docker-compose.dev.yml exec postgres psql -U taskflow -d taskqueue -c "SELECT 1;"
```

### Test Redis Connection

```bash
# From host
redis-cli ping

# Or in container
docker-compose -f deployment/docker/docker-compose.dev.yml exec redis redis-cli ping
```

### Test API

```bash
curl http://localhost:8000/health
```

## Using Makefile (Simpler)

If you prefer, use the Makefile for convenience:

```bash
# Development stack
make docker-up-dev

# Production stack
make docker-up-prod

# Stop all
make docker-down

# View logs
make docker-logs

# Clean up (remove volumes)
make docker-clean
```

## Rebuild Containers

If you've made changes to the code or want a fresh build:

```bash
# Rebuild without cache
docker-compose -f deployment/docker/docker-compose.prod.yml build --no-cache

# Then start
docker-compose -f deployment/docker/docker-compose.prod.yml up -d
```

## Development Workflow

1. **Start development stack**:

   ```bash
   docker-compose -f deployment/docker/docker-compose.dev.yml up -d
   ```

2. **Create virtual environment** (on host):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies** (on host):

   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

4. **Run API** (on host, connects to Docker containers):

   ```bash
   python run.py
   ```

5. **Run worker** (on host):

   ```bash
   python -m src.worker.main
   ```

6. **Run tests**:
   ```bash
   pytest
   ```

## Production Deployment

1. **Start full stack**:

   ```bash
   docker-compose -f deployment/docker/docker-compose.prod.yml up -d
   ```

2. **Initialize database**:

   ```bash
   docker-compose -f deployment/docker/docker-compose.prod.yml exec api alembic upgrade head
   ```

3. **Verify health**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:9090/graph  # Prometheus
   curl http://localhost:3001        # Grafana (admin/admin)
   ```

## Cleanup

### Remove Stopped Containers

```bash
docker container prune
```

### Remove Unused Images

```bash
docker image prune
```

### Remove All Volumes (Data Loss!)

```bash
docker volume prune
```

### Complete Reset

```bash
docker-compose -f deployment/docker/docker-compose.prod.yml down -v
# This removes all data in PostgreSQL and Redis!
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :5432      # PostgreSQL
lsof -i :6379      # Redis
lsof -i :8000      # API

# Kill process
kill -9 <PID>
```

### Container Won't Start

```bash
# Check logs
docker-compose -f deployment/docker/docker-compose.dev.yml logs postgres

# Inspect container
docker inspect container_name
```

### Connection Refused

```bash
# Wait for service health checks
docker-compose -f deployment/docker/docker-compose.dev.yml ps

# Check service is healthy
docker inspect taskflow_postgres | grep Health
```

### Permission Denied

```bash
# Run docker with sudo if needed
sudo docker-compose -f deployment/docker/docker-compose.dev.yml up -d
```

## See Also

- [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) - Full deployment instructions
- [REQUIREMENTS_AND_SETUP.md](REQUIREMENTS_AND_SETUP.md) - System requirements
- Dockerfile.api, Dockerfile.worker - Container images
