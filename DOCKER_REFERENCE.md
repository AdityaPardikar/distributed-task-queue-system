# Docker Configuration Reference

**Actual files are located in**: `deployment/docker/`

See `docs/deployment/DOCKER_USAGE.md` for complete Docker commands and workflow.

## Quick Start

### Development (PostgreSQL + Redis only)

```bash
docker-compose -f deployment/docker/docker-compose.dev.yml up -d
```

### Full Stack (with API, Worker, Prometheus, Grafana)

```bash
docker-compose -f deployment/docker/docker-compose.prod.yml up -d
```

### Stop Services

```bash
docker-compose -f deployment/docker/docker-compose.dev.yml down
```

## Files

| File                    | Purpose                 | Location           |
| ----------------------- | ----------------------- | ------------------ |
| docker-compose.dev.yml  | Local development stack | deployment/docker/ |
| docker-compose.prod.yml | Production stack        | deployment/docker/ |
| Dockerfile.api          | API container image     | deployment/docker/ |
| Dockerfile.worker       | Worker container image  | deployment/docker/ |

## Documentation

See: `docs/deployment/` folder

- **DOCKER_USAGE.md** - Complete Docker reference
- **DEPLOYMENT_GUIDE.md** - Full deployment instructions
