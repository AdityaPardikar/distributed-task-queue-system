# Distributed Task Queue System - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [Docker Deployment](#docker-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Monitoring & Observability](#monitoring--observability)
8. [Troubleshooting](#troubleshooting)
9. [Performance Tuning](#performance-tuning)

---

## Prerequisites

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **Python**: 3.9+
- **PostgreSQL**: 12+
- **Redis**: 6.0+
- **Memory**: 4GB minimum (8GB recommended)
- **CPU**: 2 cores minimum (4+ cores recommended)

### Required Services

```bash
# PostgreSQL
psql --version  # >= 12

# Redis
redis-cli --version  # >= 6.0
```

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd distributed-task-queue-system
```

### 2. Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb task_queue

# Run migrations
alembic upgrade head
```

### 5. Redis Verification

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```env
# Application
APP_NAME=DistributedTaskQueue
VERSION=1.0.0
LOG_LEVEL=INFO
LOG_FORMAT=json

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/task_queue
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_POOL_RECYCLE=3600

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# API
API_HOST=0.0.0.0
API_PORT=8000
WORKERS_API_PORT=8001

# Monitoring
METRICS_ENABLED=true
TRACING_ENABLED=true
TRACING_ENDPOINT=http://localhost:4318

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000

# Task Settings
TASK_TIMEOUT_SECONDS=300
MAX_RETRY_ATTEMPTS=3
RETRY_BACKOFF_MULTIPLIER=2
```

### Configuration File

Create `config.yaml`:

```yaml
database:
  url: postgresql://user:password@localhost:5432/task_queue
  pool_size: 20
  echo: false

redis:
  host: localhost
  port: 6379
  db: 0

broker:
  queue_type: redis
  priority_queues: true
  max_queue_depth: 10000

workers:
  default_capacity: 5
  heartbeat_interval: 30
  heartbeat_timeout: 300

tasks:
  timeout_seconds: 300
  max_retries: 3
  retry_backoff_seconds: 5

monitoring:
  enabled: true
  prometheus_port: 9090
  metrics_enabled: true

tracing:
  enabled: true
  service_name: task-queue
  endpoint: http://localhost:4318
```

---

## Running the System

### Development Mode

```bash
# Start FastAPI server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start a worker
python -m src.worker.main

# In another terminal, start scheduler
python -m src.scheduler.main
```

### Production Mode

```bash
# Using Gunicorn with multiple workers
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
# Expected response:
# {"status": "healthy", "version": "1.0.0"}
```

---

## Docker Deployment

### Build Docker Image

```bash
# Build API image
docker build -f Dockerfile.api -t task-queue-api:latest .

# Build Worker image
docker build -f Dockerfile.worker -t task-queue-worker:latest .

# Build Scheduler image
docker build -f Dockerfile.scheduler -t task-queue-scheduler:latest .
```

### Docker Compose (Development)

```bash
docker-compose -f docker-compose.yml up -d

# Check logs
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f scheduler

# Stop services
docker-compose down
```

### Docker Compose Production Stack

```yaml
version: "3.9"
services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: task_queue
      POSTGRES_USER: task_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  api:
    image: task-queue-api:latest
    environment:
      DATABASE_URL: postgresql://task_user:secure_password@postgres:5432/task_queue
      REDIS_HOST: redis
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    scale: 2

  worker:
    image: task-queue-worker:latest
    environment:
      DATABASE_URL: postgresql://task_user:secure_password@postgres:5432/task_queue
      REDIS_HOST: redis
    depends_on:
      - postgres
      - redis
    scale: 3

volumes:
  postgres_data:
  redis_data:
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.21+)
- kubectl configured
- Helm 3+ (optional)

### Deployment with kubectl

```bash
# Create namespace
kubectl create namespace task-queue

# Create ConfigMap
kubectl create configmap task-queue-config \
  --from-file=config.yaml \
  -n task-queue

# Create secrets
kubectl create secret generic postgres-credentials \
  --from-literal=username=task_user \
  --from-literal=password=secure_password \
  -n task-queue

# Deploy services
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/scheduler-deployment.yaml

# Check deployment status
kubectl get deployments -n task-queue
kubectl get pods -n task-queue
```

### Example Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: task-queue-api
  namespace: task-queue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: task-queue-api
  template:
    metadata:
      labels:
        app: task-queue-api
    spec:
      containers:
        - name: api
          image: task-queue-api:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: url
            - name: REDIS_HOST
              value: redis-service
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
```

---

## Monitoring & Observability

### Prometheus Metrics

```bash
# Metrics endpoint
curl http://localhost:8000/metrics

# View specific metrics
curl http://localhost:8000/metrics | grep task_queue
```

### OpenTelemetry Tracing

Configure OTLP exporter:

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318")
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Log with context
logger.info(
    "task_submitted",
    task_id="123e4567-e89b-12d3-a456-426614174000",
    task_name="process_data",
    priority=5
)
```

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Worker health
curl http://localhost:8001/health

# Database health
curl http://localhost:8000/api/v1/health/database

# Redis health
curl http://localhost:8000/api/v1/health/redis
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U task_user -d task_queue -h localhost

# Check connection pooling
SELECT * FROM pg_stat_activity;

# View connection settings
SHOW max_connections;
```

### Redis Connection Issues

```bash
# Test Redis
redis-cli -h localhost -p 6379 PING

# View Redis info
redis-cli INFO

# Check memory usage
redis-cli INFO memory
```

### Task Queue Backlog

```bash
# Check queue depth
curl http://localhost:8000/api/v1/dashboard/queue-depth

# View pending tasks
curl http://localhost:8000/api/v1/tasks?status=PENDING&limit=100

# Analyze bottleneck
curl http://localhost:8000/api/v1/analytics/trends?hours=1
```

### Worker Issues

```bash
# View active workers
curl http://localhost:8000/api/v1/workers

# Check worker health
curl http://localhost:8000/api/v1/workers/status/all

# View worker metrics
curl http://localhost:8000/api/v1/metrics/workers
```

### Common Issues & Solutions

**Issue: "Unable to connect to PostgreSQL"**

- Verify PostgreSQL is running
- Check DATABASE_URL environment variable
- Verify credentials and database exists

**Issue: "Redis connection timeout"**

- Check Redis is running on configured host/port
- Verify firewall allows connection
- Check Redis memory/performance

**Issue: "Tasks stuck in RUNNING state"**

- Check worker heartbeat intervals
- Verify worker timeout configuration
- View execution logs for errors

**Issue: "High queue depth"**

- Increase worker capacity
- Scale up worker count
- Optimize task execution time

---

## Performance Tuning

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_task_status ON tasks(status);
CREATE INDEX idx_task_priority ON tasks(priority DESC);
CREATE INDEX idx_task_created ON tasks(created_at DESC);
CREATE INDEX idx_worker_status ON workers(status);

-- Check index usage
SELECT * FROM pg_stat_user_indexes;
```

### Redis Optimization

```bash
# Monitor Redis memory
redis-cli INFO memory

# Optimize key expiration
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Enable persistence (AOF)
redis-cli CONFIG SET appendonly yes
```

### Connection Pooling

```env
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_POOL_PRE_PING=true
```

### Worker Configuration

```env
# Optimal worker capacity
WORKER_CAPACITY=10

# Heartbeat settings
WORKER_HEARTBEAT_INTERVAL=30
WORKER_HEARTBEAT_TIMEOUT=300

# Task timeout
TASK_TIMEOUT_SECONDS=300
```

---

## Scaling Guidelines

### Horizontal Scaling

1. **API Servers**: Scale independently (stateless)
2. **Workers**: Scale based on task load and complexity
3. **Database**: Use connection pooling, consider read replicas
4. **Redis**: Use Redis Cluster for high throughput

### Vertical Scaling

- Increase worker capacity (tasks per worker)
- Optimize task execution time
- Increase database/Redis resources

### Load Balancing

```nginx
upstream task_queue_api {
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

server {
    listen 80;
    location /api {
        proxy_pass http://task_queue_api;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup PostgreSQL
pg_dump task_queue > backup_$(date +%Y%m%d).sql

# Restore from backup
psql task_queue < backup_20260125.sql
```

### Redis Backup

```bash
# Trigger Redis save
redis-cli BGSAVE

# Backup RDB file
cp /var/lib/redis/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

---

## Security Hardening

### Database Security

```sql
-- Create separate user with limited privileges
CREATE USER task_worker WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE task_queue TO task_worker;
GRANT USAGE ON SCHEMA public TO task_worker;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO task_worker;
```

### Redis Security

```bash
# Set password
redis-cli CONFIG SET requirepass secure_password

# Only listen on localhost
redis-cli CONFIG SET bind 127.0.0.1

# Disable dangerous commands
redis-cli CONFIG SET rename-command FLUSHDB ""
```

### API Security

```env
SECRET_KEY=generate_strong_secret_key_here
ALLOWED_HOSTS=api.example.com
CORS_ORIGINS=https://app.example.com
HTTPS_ONLY=true
```

---

## Support & Contact

For issues and questions:

- GitHub Issues: https://github.com/AdityaPardikar/distributed-task-queue-system/issues
- Email: support@taskqueue.io
- Documentation: https://docs.taskqueue.io
