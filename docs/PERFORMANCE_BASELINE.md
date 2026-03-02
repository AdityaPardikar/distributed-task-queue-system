# Performance Baseline — TaskFlow v1.0.0

> Baseline performance characteristics for regression testing and capacity planning.

---

## Test Environment

| Parameter   | Value                           |
| ----------- | ------------------------------- |
| CPU         | 4 cores (Docker resource limit) |
| Memory      | 4 GB (Docker resource limit)    |
| PostgreSQL  | 15, shared_buffers=256MB        |
| Redis       | 7, maxmemory=512MB              |
| API Workers | 4 (uvicorn workers)             |
| Python      | 3.13                            |

---

## API Response Times (p50 / p95 / p99)

| Endpoint                       | p50  | p95  | p99   | RPS  |
| ------------------------------ | ---- | ---- | ----- | ---- |
| `GET /health`                  | 2ms  | 5ms  | 10ms  | 5000 |
| `GET /ready`                   | 3ms  | 8ms  | 15ms  | 4000 |
| `POST /api/v1/auth/login`      | 15ms | 35ms | 50ms  | 500  |
| `POST /api/v1/tasks`           | 12ms | 25ms | 40ms  | 1000 |
| `GET /api/v1/tasks`            | 8ms  | 20ms | 35ms  | 2000 |
| `GET /api/v1/tasks/{id}`       | 5ms  | 12ms | 20ms  | 3000 |
| `GET /api/v1/workers`          | 6ms  | 15ms | 25ms  | 2500 |
| `GET /api/v1/dashboard/stats`  | 20ms | 45ms | 70ms  | 800  |
| `GET /api/v1/search?q=...`     | 25ms | 55ms | 90ms  | 600  |
| `GET /api/v1/metrics`          | 10ms | 20ms | 30ms  | 2000 |
| `GET /api/v1/analytics/trends` | 30ms | 65ms | 100ms | 400  |

---

## Throughput Targets

| Metric                          | Target          | Notes                           |
| ------------------------------- | --------------- | ------------------------------- |
| Task creation rate              | 1,000 tasks/sec | Single API instance             |
| Task processing rate            | 100K+ tasks/hr  | 4 workers, mixed priority       |
| Concurrent connections          | 1,000+          | WebSocket + HTTP combined       |
| Queue depth before backpressure | 50,000 tasks    | Redis memory-dependent          |
| WebSocket broadcast latency     | < 50ms          | Event bus → client notification |

---

## Resource Utilization (Steady State)

| Service    | CPU (avg) | CPU (peak) | Memory (avg) | Memory (peak) |
| ---------- | --------- | ---------- | ------------ | ------------- |
| API        | 15%       | 40%        | 200 MB       | 400 MB        |
| PostgreSQL | 10%       | 30%        | 300 MB       | 500 MB        |
| Redis      | 5%        | 15%        | 80 MB        | 200 MB        |
| Frontend   | < 1%      | 2%         | 50 MB        | 80 MB         |
| Nginx      | < 1%      | 5%         | 20 MB        | 40 MB         |

---

## Database Metrics

| Query Pattern               | Avg Time | Index Used          |
| --------------------------- | -------- | ------------------- |
| Task lookup by ID           | 0.5ms    | PK (btree)          |
| Task list with pagination   | 3ms      | status + created_at |
| Full-text search            | 15ms     | GIN (tsvector)      |
| Worker heartbeat update     | 1ms      | PK (btree)          |
| Campaign recipient count    | 5ms      | campaign_id FK      |
| Analytics aggregation (24h) | 25ms     | created_at          |

---

## Scaling Guidelines

### Horizontal Scaling

| Load Level           | API Instances | Workers | PostgreSQL            | Redis           |
| -------------------- | ------------- | ------- | --------------------- | --------------- |
| Low (< 1K tasks/hr)  | 1             | 1       | Single instance       | Single instance |
| Medium (1K-50K/hr)   | 2-3           | 2-4     | Single + read replica | Single          |
| High (50K-500K/hr)   | 4-8           | 4-8     | Primary + 2 replicas  | Sentinel        |
| Very High (500K+/hr) | 8+            | 8+      | Sharded / Citus       | Cluster         |

### Bottleneck Indicators

| Symptom                        | Likely Bottleneck      | Action                                |
| ------------------------------ | ---------------------- | ------------------------------------- |
| API response time > 200ms p95  | API CPU / connections  | Scale API horizontally                |
| Queue depth growing steadily   | Worker throughput      | Add worker instances                  |
| DB connection pool exhaustion  | PostgreSQL connections | Increase pool size or add pgBouncer   |
| Redis memory > 80%             | Cache/queue overflow   | Increase maxmemory or eviction policy |
| WebSocket disconnect rate > 1% | Connection limits      | Scale Nginx / increase limits         |

---

## Smoke Test Baseline

Run `python scripts/smoke_test.py` after deployment. Expected results:

| Test                 | Expected | Max Duration |
| -------------------- | -------- | ------------ |
| Health Check         | PASS     | 50ms         |
| Readiness Probe      | PASS     | 100ms        |
| Liveness Probe       | PASS     | 50ms         |
| User Registration    | PASS     | 200ms        |
| User Login (JWT)     | PASS     | 200ms        |
| Create Task          | PASS     | 150ms        |
| List Tasks           | PASS     | 100ms        |
| Dashboard Stats      | PASS     | 200ms        |
| Metrics Endpoint     | PASS     | 100ms        |
| WebSocket Connection | PASS     | 500ms        |

**All 16 smoke tests must pass before a release is considered healthy.**
