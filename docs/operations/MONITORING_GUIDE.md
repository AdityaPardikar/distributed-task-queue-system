# Monitoring & Observability Guide

## Overview

Complete guide to monitoring, observability, and troubleshooting the Distributed Task Queue System.

---

## Table of Contents

1. [Metrics & Prometheus](#metrics--prometheus)
2. [Distributed Tracing](#distributed-tracing)
3. [Structured Logging](#structured-logging)
4. [Health Checks](#health-checks)
5. [Dashboards](#dashboards)
6. [Alerting](#alerting)
7. [Troubleshooting](#troubleshooting)

---

## Metrics & Prometheus

### Metrics Endpoints

- **Prometheus**: `http://localhost:8000/metrics`
- **Metrics Format**: OpenMetrics (Prometheus text format)

### Key Metrics

#### Task Metrics

```
# Task submission rate (tasks per minute)
task_queue:submission_rate

# Task completion rate
task_queue:completion_rate

# Task failure rate
task_queue:failure_rate

# Task processing time (p50, p95, p99)
task_queue:processing_time_seconds_bucket

# Queue depth by priority
task_queue:queue_depth{priority="high"}
task_queue:queue_depth{priority="normal"}
task_queue:queue_depth{priority="low"}

# Retry rate
task_queue:retry_rate

# Task timeout rate
task_queue:timeout_rate
```

#### Worker Metrics

```
# Worker count by status
workers:total{status="active"}
workers:total{status="paused"}
workers:total{status="draining"}

# Worker utilization
worker:utilization_percent{worker_id="worker-1"}

# Worker task rate (tasks per minute)
worker:task_rate{worker_id="worker-1"}

# Worker average execution time
worker:avg_duration_seconds{worker_id="worker-1"}

# Worker error rate
worker:error_rate{worker_id="worker-1"}

# Worker uptime
worker:uptime_seconds{worker_id="worker-1"}

# Worker restart count
worker:restart_count{worker_id="worker-1"}
```

#### System Metrics

```
# CPU usage
system:cpu_usage_percent

# Memory usage
system:memory_usage_percent

# Disk usage
system:disk_usage_percent

# Network I/O
system:network_in_bytes
system:network_out_bytes
```

#### Database Metrics

```
# Connection pool utilization
database:pool_connections_in_use
database:pool_connections_available

# Query duration
database:query_duration_seconds_bucket

# Query count
database:queries_total{type="insert"}
database:queries_total{type="select"}
database:queries_total{type="update"}
```

#### Redis Metrics

```
# Connected clients
redis:connected_clients

# Memory usage
redis:memory_bytes

# Commands per second
redis:commands_total

# Keys by type
redis:keys_by_type{type="string"}
redis:keys_by_type{type="list"}
redis:keys_by_type{type="hash"}
```

### Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "task-queue"
    static_configs:
      - targets: ["localhost:8000"]
    metrics_path: "/metrics"

  - job_name: "database"
    static_configs:
      - targets: ["localhost:5432"]

  - job_name: "redis"
    static_configs:
      - targets: ["localhost:6379"]

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - "localhost:9093"

rule_files:
  - "alert_rules.yml"
```

### Common Queries

```promql
# Task success rate (last hour)
rate(task_queue:completion_rate[1h]) / (rate(task_queue:submission_rate[1h]) + 0.001)

# Average task processing time
avg(task_queue:processing_time_seconds)

# Queue backlog
sum(task_queue:queue_depth)

# Worker utilization by worker
worker:utilization_percent

# Failed tasks in last hour
rate(task_queue:failure_rate[1h])

# P99 task latency
histogram_quantile(0.99, task_queue:processing_time_seconds_bucket)
```

---

## Distributed Tracing

### OpenTelemetry Integration

System uses OpenTelemetry for distributed tracing with OTLP exporter.

### Trace Configuration

Environment variables:

```env
TRACING_ENABLED=true
TRACING_ENDPOINT=http://localhost:4318
TRACING_SAMPLE_RATE=0.1
```

### Key Spans

#### Task Submission

```
Span: task:submit
  - parent: api:endpoint
  - attributes:
    - task.id
    - task.name
    - task.priority
    - queue.name
```

#### Task Execution

```
Span: task:execute
  - parent: task:submit
  - attributes:
    - task.id
    - worker.id
    - task.status
    - duration_ms
```

#### Worker Operations

```
Span: worker:heartbeat
Span: worker:register
Span: worker:deregister
  - attributes:
    - worker.id
    - worker.hostname
    - worker.status
```

### Tracing Setup with Jaeger

1. **Start Jaeger**:

```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 4318:4318 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest
```

2. **Access Jaeger UI**: http://localhost:16686

3. **Query Traces**:

- Service: `task-queue`
- Operation: `task:execute`, `worker:heartbeat`, etc.

---

## Structured Logging

### Log Configuration

```python
import structlog

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### Log Levels

- **DEBUG**: Detailed information (10,000+ messages/hour)
- **INFO**: General information
- **WARNING**: Potential issues
- **ERROR**: Error events
- **CRITICAL**: Critical events

### Example Logs

#### Task Submission

```json
{
  "timestamp": "2026-01-25T14:00:00.000Z",
  "level": "INFO",
  "logger": "task_service",
  "event": "task_submitted",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "process_payment",
  "priority": 8,
  "queue": "payments",
  "request_id": "req-uuid"
}
```

#### Task Execution

```json
{
  "timestamp": "2026-01-25T14:05:00.000Z",
  "level": "INFO",
  "logger": "task_executor",
  "event": "task_execution_complete",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "worker_id": "worker-1",
  "duration_ms": 4850,
  "status": "COMPLETED",
  "request_id": "req-uuid"
}
```

#### Worker Heartbeat

```json
{
  "timestamp": "2026-01-25T14:00:30.000Z",
  "level": "DEBUG",
  "logger": "worker_service",
  "event": "worker_heartbeat",
  "worker_id": "worker-1",
  "current_load": 3,
  "capacity": 5,
  "uptime_seconds": 86400
}
```

---

## Health Checks

### Health Endpoint

**GET** `/health`

Returns overall system health status.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-25T14:00:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2
    },
    "workers": {
      "status": "healthy",
      "active_count": 5,
      "total_count": 8
    },
    "api": {
      "status": "healthy",
      "uptime_seconds": 7200
    }
  }
}
```

### Component Health Checks

#### Database Health

```bash
curl http://localhost:8000/api/v1/health/database
```

Response:

```json
{
  "status": "healthy",
  "connection_pool": {
    "active": 8,
    "idle": 12,
    "total": 20
  },
  "query_latency_ms": 5.2
}
```

#### Redis Health

```bash
curl http://localhost:8000/api/v1/health/redis
```

Response:

```json
{
  "status": "healthy",
  "memory_mb": 512,
  "connected_clients": 10,
  "ops_per_second": 1200
}
```

#### Worker Health

```bash
curl http://localhost:8000/api/v1/health/workers
```

Response:

```json
{
  "status": "healthy",
  "active_workers": 5,
  "total_workers": 8,
  "healthy_workers": 7,
  "unhealthy_workers": 1
}
```

---

## Dashboards

### Grafana Setup

1. **Start Grafana**:

```bash
docker run -d --name grafana \
  -p 3000:3000 \
  grafana/grafana:latest
```

2. **Add Prometheus Data Source**:

- URL: `http://prometheus:9090`
- Scrape Interval: 15s

3. **Import Dashboards**:

- Task Queue Overview
- Worker Performance
- System Metrics
- Error Analysis

### Key Dashboard Panels

#### Task Queue Overview

- Queue depth over time
- Task submission rate
- Task completion rate
- Failure rate
- Average processing time

#### Worker Performance

- Worker utilization (%)
- Task rate by worker
- Error rate by worker
- Uptime by worker
- Task distribution

#### System Health

- CPU usage
- Memory usage
- Disk I/O
- Network throughput
- Database connections

---

## Alerting

### Alert Rules

Create `alert_rules.yml`:

```yaml
groups:
  - name: task_queue
    interval: 1m
    rules:
      - alert: HighQueueDepth
        expr: sum(task_queue:queue_depth) > 1000
        for: 5m
        annotations:
          summary: "Queue depth exceeded 1000"

      - alert: HighFailureRate
        expr: rate(task_queue:failure_rate[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Task failure rate > 10%"

      - alert: NoActiveWorkers
        expr: count(up{job="workers"}) == 0
        for: 1m
        annotations:
          summary: "No active workers"

      - alert: WorkerUnhealthy
        expr: up{job="workers"} == 0
        for: 5m
        annotations:
          summary: "Worker unhealthy: {{ $labels.instance }}"

      - alert: DatabaseConnectionPoolExhausted
        expr: database:pool_connections_available < 2
        for: 5m
        annotations:
          summary: "Database connection pool almost exhausted"
```

### Alert Routing

Configure AlertManager for notifications:

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: "slack"
  group_by: ["severity", "service"]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h

receivers:
  - name: "slack"
    slack_configs:
      - api_url: "YOUR_SLACK_WEBHOOK_URL"
        channel: "#alerts"
        text: "{{ .GroupLabels.alertname }}"
```

---

## Troubleshooting

### High Queue Depth

**Symptoms**: Queue depth > 1000, growing rapidly

**Diagnosis**:

```bash
# Check submission rate vs completion rate
curl http://localhost:8000/api/v1/dashboard/stats

# View queue depth by priority
curl http://localhost:8000/api/v1/dashboard/queue-depth

# Check for stuck tasks
curl "http://localhost:8000/api/v1/tasks?status=RUNNING&limit=100"
```

**Solutions**:

1. Scale up workers
2. Increase worker capacity
3. Optimize task execution time
4. Check for failures in retry queue

### High Failure Rate

**Symptoms**: Failure rate > 5%

**Diagnosis**:

```bash
# Get failure patterns
curl http://localhost:8000/api/v1/analytics/trends

# Find failing tasks
curl "http://localhost:8000/api/v1/search/tasks?status=FAILED"

# Check DLQ
curl "http://localhost:8000/api/v1/tasks?in_dlq=true"
```

**Solutions**:

1. Review error messages
2. Check worker logs
3. Validate task arguments
4. Review recent code changes

### Worker Unhealthy

**Symptoms**: Worker not accepting tasks, high error rate

**Diagnosis**:

```bash
# Check worker status
curl http://localhost:8000/api/v1/workers/{worker_id}/status

# Check worker logs
docker logs worker-container

# Check worker metrics
curl "http://localhost:8000/api/v1/metrics/workers/{worker_id}"
```

**Solutions**:

1. Restart worker
2. Check resource constraints
3. Verify database/Redis connectivity
4. Scale down if overloaded

### Database Performance

**Symptoms**: Slow queries, high latency

**Diagnosis**:

```bash
# Check slow queries
SELECT query, calls, total_time FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;

# Check index usage
SELECT * FROM pg_stat_user_indexes;

# Check locks
SELECT * FROM pg_locks;
```

**Solutions**:

1. Add missing indexes
2. Optimize queries
3. Increase connection pool size
4. Use read replicas

---

## SLO & SLA

### Service Level Objectives

- **Task Success Rate**: 99%+
- **Task Processing Latency**: p99 < 30 seconds
- **API Availability**: 99.9%
- **Worker Health**: 95%+ healthy

### Monitoring SLOs

```promql
# Task success rate
sum(rate(task_queue:completion_rate[5m])) / sum(rate(task_queue:submission_rate[5m]))

# API availability
sum(rate(api:requests{status=~"2.."}[5m])) / sum(rate(api:requests[5m]))

# Worker health rate
count(workers:healthy) / count(workers:total)
```

---

## Support

For monitoring questions:

- Documentation: https://docs.taskqueue.io
- Community: GitHub Discussions
- Enterprise: contact support@taskqueue.io
