# Operational Runbook — TaskFlow

> **Version:** 1.0.0 | **Last Updated:** 2026-03-02 | **Audience:** DevOps, SRE, On-Call Engineers

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Service Architecture](#service-architecture)
3. [Startup Procedures](#startup-procedures)
4. [Shutdown Procedures](#shutdown-procedures)
5. [Scaling](#scaling)
6. [Backup & Restore](#backup--restore)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Incident Response](#incident-response)
9. [Rollback Procedures](#rollback-procedures)
10. [Maintenance Tasks](#maintenance-tasks)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Contact & Escalation](#contact--escalation)

---

## System Overview

TaskFlow is a distributed task queue system composed of:

| Component    | Technology           | Port | Health Endpoint  |
| ------------ | -------------------- | ---- | ---------------- |
| API Server   | FastAPI / Uvicorn    | 8000 | `GET /health`    |
| Frontend     | React / Vite / Nginx | 5173 | HTTP 200 on `/`  |
| PostgreSQL   | PostgreSQL 15 Alpine | 5432 | `pg_isready`     |
| Redis        | Redis 7 Alpine       | 6379 | `redis-cli ping` |
| Nginx (prod) | Nginx 1.25 Alpine    | 80   | HTTP 200 on `/`  |
| Prometheus   | Prometheus 2.x       | 9090 | `/-/healthy`     |
| Grafana      | Grafana 10.x         | 3001 | `/api/health`    |
| cAdvisor     | cAdvisor 0.47        | 8080 | `/healthz`       |

---

## Service Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Nginx     │───▶│  Frontend   │    │  Prometheus  │
│  (reverse   │    │  (React)    │    │  (metrics)   │
│   proxy)    │───▶│             │    └──────┬───────┘
└─────────────┘    └─────────────┘           │
       │                                     │
       ▼                                     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  API Server │───▶│ PostgreSQL  │    │   Grafana    │
│  (FastAPI)  │    │   (data)    │    │ (dashboards) │
│             │───▶│             │    └─────────────┘
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│    Redis     │
│  (broker +   │
│   cache)     │
└─────────────┘
```

---

## Startup Procedures

### Development Environment

```bash
# 1. Start infrastructure
docker compose up -d postgres redis

# 2. Wait for services
until pg_isready -h localhost -p 5432; do sleep 1; done

# 3. Run migrations
alembic upgrade head

# 4. Seed data (optional)
python scripts/seed_data.py

# 5. Start API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 6. Start frontend (separate terminal)
cd frontend && npm run dev
```

### Production Environment

```bash
# 1. Validate environment
python scripts/validate_env.py

# 2. Start all services
docker compose -f docker-compose.prod.yml --env-file .env up -d

# 3. Verify health
curl -s http://localhost/health | jq .
curl -s http://localhost/ready | jq .

# 4. Check all containers
docker compose -f docker-compose.prod.yml ps

# 5. Verify logs (no errors)
docker compose -f docker-compose.prod.yml logs --tail=50 api
```

### Startup Verification Checklist

- [ ] PostgreSQL accepting connections (`pg_isready`)
- [ ] Redis responding to PING
- [ ] API returns `{"status": "healthy"}` on `/health`
- [ ] API returns ready on `/ready` (DB + Redis connected)
- [ ] Frontend loads at port 80 (prod) or 5173 (dev)
- [ ] Prometheus scraping metrics at `/api/v1/metrics/prometheus`
- [ ] Grafana dashboards loading at port 3001

---

## Shutdown Procedures

### Graceful Shutdown

```bash
# 1. Drain workers (finish current tasks, reject new ones)
curl -X POST http://localhost:8000/api/v1/workers/{worker_id}/drain

# 2. Wait for in-flight tasks to complete (check queue depth)
watch -n 5 'curl -s http://localhost:8000/api/v1/dashboard/queue-depth | jq .'

# 3. Stop services in order
docker compose -f docker-compose.prod.yml stop api
docker compose -f docker-compose.prod.yml stop frontend nginx
docker compose -f docker-compose.prod.yml stop prometheus grafana cadvisor
docker compose -f docker-compose.prod.yml stop redis
docker compose -f docker-compose.prod.yml stop postgres
```

### Emergency Shutdown

```bash
# Immediate stop all services
docker compose -f docker-compose.prod.yml down

# Force kill if needed
docker compose -f docker-compose.prod.yml kill
```

> **Warning:** Emergency shutdown may leave tasks in `RUNNING` state. Run cleanup after restart:
>
> ```bash
> curl -X POST http://localhost:8000/api/v1/performance/tasks/batch/requeue-failed
> ```

---

## Scaling

### Horizontal Scaling — API

```bash
# Scale API replicas (requires load balancer)
docker compose -f docker-compose.prod.yml up -d --scale api=3
```

### Vertical Scaling — Resource Limits

Edit `docker-compose.prod.yml` deploy resources:

```yaml
deploy:
  resources:
    limits:
      cpus: "2.0" # Increase from 1.0
      memory: 1024M # Increase from 512M
```

### Database Connection Pool

Adjust in `.env`:

```ini
DB_POOL_SIZE=20          # Default: 5
DB_MAX_OVERFLOW=30       # Default: 10
DB_POOL_TIMEOUT=60       # Default: 30
```

### Redis Memory

```bash
# Check current memory usage
redis-cli INFO memory | grep used_memory_human

# Set max memory
redis-cli CONFIG SET maxmemory 512mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## Backup & Restore

### Automated Backup via API

```bash
# Create backup
curl -X POST http://localhost:8000/api/v1/operations/backups \
  -H "Authorization: Bearer $TOKEN" | jq .

# List existing backups
curl http://localhost:8000/api/v1/operations/backups \
  -H "Authorization: Bearer $TOKEN" | jq .

# Verify backup integrity
curl -X POST http://localhost:8000/api/v1/operations/backups/verify \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Manual PostgreSQL Backup

```bash
# Dump entire database
docker exec dtqs-postgres-prod pg_dump -U taskflow -d taskflow \
  --format=custom --file=/tmp/backup_$(date +%Y%m%d_%H%M%S).dump

# Copy backup out of container
docker cp dtqs-postgres-prod:/tmp/backup_*.dump ./backups/
```

### Restore from Backup

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/operations/backups/restore \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_id": "backup_20260302"}' | jq .

# Via pg_restore
docker exec -i dtqs-postgres-prod pg_restore -U taskflow -d taskflow \
  --clean --if-exists < ./backups/backup_20260302.dump
```

### Backup Schedule (Recommended)

| Frequency | Type        | Retention |
| --------- | ----------- | --------- |
| Hourly    | Incremental | 24 hours  |
| Daily     | Full dump   | 7 days    |
| Weekly    | Full dump   | 4 weeks   |
| Monthly   | Full dump   | 12 months |

### Cleanup Old Backups

```bash
curl -X POST http://localhost:8000/api/v1/operations/backups/cleanup \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"keep_count": 7}' | jq .
```

---

## Monitoring & Alerting

### Dashboards

| Dashboard           | URL                                  | Purpose                      |
| ------------------- | ------------------------------------ | ---------------------------- |
| Task Queue Overview | `http://localhost:3001/d/task-queue` | Task throughput, queue depth |
| Worker Performance  | `http://localhost:3001/d/workers`    | Worker utilization, health   |
| System Health       | `http://localhost:3001/d/system`     | CPU, memory, disk, network   |
| API Server          | `http://localhost:8000/docs`         | Interactive API docs         |

### Key Metrics to Watch

| Metric                        | Warning Threshold | Critical Threshold |
| ----------------------------- | ----------------- | ------------------ |
| `taskflow_queue_depth`        | > 1,000           | > 10,000           |
| `taskflow_tasks_failed_total` | > 50/min          | > 200/min          |
| `taskflow_workers_active`     | < 2               | 0                  |
| API response time (p95)       | > 500ms           | > 2,000ms          |
| PostgreSQL connections        | > 80%             | > 95%              |
| Redis memory usage            | > 70%             | > 90%              |
| Disk usage                    | > 75%             | > 90%              |

### Alert Response Actions

| Alert                    | Action                                              |
| ------------------------ | --------------------------------------------------- |
| High queue depth         | Scale workers, check for stuck tasks                |
| High failure rate        | Check logs, review error patterns via analytics API |
| No active workers        | Restart worker containers, check heartbeats         |
| High API latency         | Check DB query performance, run ANALYZE             |
| DB connection exhaustion | Increase pool size, check for connection leaks      |
| Redis memory critical    | Flush expired keys, increase maxmemory              |

---

## Incident Response

### Severity Levels

| Level | Description               | Response Time | Escalation               |
| ----- | ------------------------- | ------------- | ------------------------ |
| SEV-1 | System down, data loss    | Immediate     | Engineering + Management |
| SEV-2 | Major feature broken      | 30 minutes    | Engineering              |
| SEV-3 | Minor feature degradation | 4 hours       | On-call                  |
| SEV-4 | Cosmetic / low impact     | Next sprint   | Backlog                  |

### Incident Workflow

1. **Detect** — Alert fires or user report
2. **Acknowledge** — Mark alert acknowledged via API
   ```bash
   curl -X POST http://localhost:8000/api/v1/alerts/{alert_id}/acknowledge \
     -H "Authorization: Bearer $TOKEN"
   ```
3. **Assess** — Check system status
   ```bash
   curl http://localhost/system/status | jq .
   ```
4. **Mitigate** — Apply temporary fix (restart, scale, throttle)
5. **Resolve** — Deploy permanent fix
6. **Postmortem** — Document root cause and action items

### Quick Diagnosis Commands

```bash
# System health overview
curl http://localhost/system/status | jq .

# Check all workers
curl http://localhost:8000/api/v1/workers/status/all \
  -H "Authorization: Bearer $TOKEN" | jq .

# View failure patterns
curl http://localhost:8000/api/v1/analytics/failure-patterns \
  -H "Authorization: Bearer $TOKEN" | jq .

# Check long-running queries
curl http://localhost:8000/api/v1/operations/queries/long-running \
  -H "Authorization: Bearer $TOKEN" | jq .

# View recent alerts
curl http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer $TOKEN" | jq .

# Docker container status
docker compose -f docker-compose.prod.yml ps
docker stats --no-stream
```

---

## Rollback Procedures

### Application Rollback

```bash
# 1. Stop current deployment
docker compose -f docker-compose.prod.yml stop api frontend

# 2. Checkout previous version
git checkout v0.9.0  # or specific commit

# 3. Rebuild and deploy
docker compose -f docker-compose.prod.yml build api frontend
docker compose -f docker-compose.prod.yml up -d api frontend

# 4. Verify health
curl http://localhost/health | jq .
```

### Database Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_hash>

# Restore from backup if migration rollback is insufficient
docker exec -i dtqs-postgres-prod pg_restore -U taskflow -d taskflow \
  --clean --if-exists < ./backups/pre_migration_backup.dump
```

### Feature Flag Rollback

```bash
# If a specific feature is causing issues, disable via config
# Edit .env and restart:
FEATURE_CHAOS_ENABLED=false
RATE_LIMIT_ENABLED=false

docker compose -f docker-compose.prod.yml restart api
```

---

## Maintenance Tasks

### Database Maintenance

```bash
# Full maintenance (VACUUM + REINDEX + ANALYZE)
curl -X POST http://localhost:8000/api/v1/operations/maintenance/full \
  -H "Authorization: Bearer $TOKEN" | jq .

# Individual operations
curl -X POST http://localhost:8000/api/v1/operations/maintenance/vacuum \
  -H "Authorization: Bearer $TOKEN" | jq .

curl -X POST http://localhost:8000/api/v1/operations/maintenance/analyze \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Task Cleanup

```bash
# Clean old completed/failed tasks (older than 30 days)
curl -X POST http://localhost:8000/api/v1/operations/maintenance/cleanup-tasks \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"older_than_days": 30}' | jq .

# Clean expired sessions
curl -X POST http://localhost:8000/api/v1/operations/maintenance/cleanup-sessions \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Scheduled Maintenance Windows

| Task                 | Frequency | Duration | Impact   |
| -------------------- | --------- | -------- | -------- |
| VACUUM ANALYZE       | Daily     | ~5 min   | None     |
| Full backup          | Daily     | ~10 min  | None     |
| Task cleanup         | Weekly    | ~2 min   | None     |
| REINDEX              | Monthly   | ~15 min  | Minimal  |
| Docker image updates | Monthly   | ~30 min  | Downtime |
| Certificate renewal  | Quarterly | ~5 min   | None     |

### Log Rotation

Docker logs are configured with:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "5"
```

Application logs use `structlog` with JSON formatting for easy parsing by log aggregation tools.

---

## Troubleshooting Guide

### API Returns 503

1. Check database connectivity:
   ```bash
   docker exec dtqs-postgres-prod pg_isready -U taskflow
   ```
2. Check Redis connectivity:
   ```bash
   docker exec dtqs-redis-prod redis-cli ping
   ```
3. Check API container logs:
   ```bash
   docker logs dtqs-api-prod --tail=100
   ```

### Tasks Stuck in RUNNING

1. Identify stale tasks:
   ```bash
   curl http://localhost:8000/api/v1/performance/tasks/stats \
     -H "Authorization: Bearer $TOKEN" | jq .
   ```
2. Cancel stale tasks (running > 1 hour):
   ```bash
   curl -X POST http://localhost:8000/api/v1/performance/tasks/batch/cancel-stale \
     -H "Authorization: Bearer $TOKEN" | jq .
   ```
3. Check worker heartbeats:
   ```bash
   curl http://localhost/workers/status | jq .
   ```

### High Memory Usage

1. Check container resource usage:
   ```bash
   docker stats --no-stream
   ```
2. Check table bloat:
   ```bash
   curl http://localhost:8000/api/v1/operations/tables/bloat \
     -H "Authorization: Bearer $TOKEN" | jq .
   ```
3. Run VACUUM:
   ```bash
   curl -X POST http://localhost:8000/api/v1/operations/maintenance/vacuum \
     -H "Authorization: Bearer $TOKEN" | jq .
   ```

### Redis Out of Memory

1. Check Redis memory:
   ```bash
   docker exec dtqs-redis-prod redis-cli INFO memory
   ```
2. Flush expired keys:
   ```bash
   docker exec dtqs-redis-prod redis-cli --scan --pattern '*:expired:*' | \
     xargs -L 1 docker exec dtqs-redis-prod redis-cli DEL
   ```
3. Set eviction policy:
   ```bash
   docker exec dtqs-redis-prod redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

### Frontend Not Loading

1. Check Nginx is proxying correctly:
   ```bash
   docker logs dtqs-nginx-prod --tail=50
   ```
2. Check frontend container:
   ```bash
   docker logs dtqs-frontend-prod --tail=50
   ```
3. Verify static files are built:
   ```bash
   docker exec dtqs-frontend-prod ls -la /usr/share/nginx/html/
   ```

---

## Contact & Escalation

| Role             | Contact              | Availability    |
| ---------------- | -------------------- | --------------- |
| On-Call Engineer | oncall@taskflow.io   | 24/7            |
| Engineering Lead | eng-lead@taskflow.io | Business hours  |
| DevOps Team      | devops@taskflow.io   | Business hours  |
| Security Team    | security@taskflow.io | pager for SEV-1 |

### Escalation Path

1. **On-Call Engineer** — First responder (15 min SLA)
2. **Engineering Lead** — If unresolved in 1 hour
3. **VP Engineering** — SEV-1 incidents only
4. **External vendor support** — PostgreSQL, Redis, Docker issues
