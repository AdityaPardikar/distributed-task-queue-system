<div align="center">

# TaskFlow — Distributed Task Queue System

**Production-grade distributed task queue with email campaign engine**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-503%2B-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-80%25%2B-brightgreen)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue)

[Quick Start](#-quick-start) •
[Features](#-features) •
[API](#-api-overview) •
[Architecture](#-architecture) •
[Documentation](#-documentation) •
[Contributing](#-contributing)

</div>

---

## Quick Start

Get the entire stack running in three steps:

```bash
# 1. Clone and enter
git clone https://github.com/yourusername/taskflow.git && cd taskflow

# 2. Start everything (API, workers, Postgres, Redis, frontend)
docker compose up -d --build

# 3. Open the dashboard
open http://localhost:5173          # Frontend
open http://localhost:8000/docs     # Swagger UI
```

> **Without Docker:** See the [manual setup](#manual-setup) section below.

---

## Features

### Task Queue Engine

- **Priority queues** — CRITICAL / HIGH / MEDIUM / LOW
- **Automatic retries** — Exponential backoff with configurable jitter
- **Task dependencies** — DAG-based execution with dependency resolution
- **Scheduled tasks** — Cron expressions via built-in scheduler
- **Dead letter queue** — Failed tasks with 30-day retention and replay
- **Workflows** — Sequential chains, parallel fan-out, conditional branching

### Email Campaign Engine

- **Campaign lifecycle** — Create, schedule, launch, pause, resume, cancel
- **Jinja2 templates** — Variable extraction, preview rendering, versioning
- **Recipient management** — Bulk import, deduplication, status tracking
- **Rate limiting** — Per-campaign send rate controls

### Real-Time Dashboard

- **React 19 SPA** — TypeScript, Tailwind CSS, Recharts
- **Live metrics** — WebSocket-powered task/worker/alert feeds
- **Task management** — Search, filter, retry, cancel, export
- **Campaign views** — Progress tracking, recipient lists, stats
- **Alert management** — Severity-based alerts with acknowledgement
- **Command palette** — Keyboard-driven navigation (Ctrl+K)

### Observability

- **Prometheus metrics** — Task throughput, latency histograms, queue depth
- **Grafana dashboards** — Pre-built panels for tasks, workers, system health
- **Structured logging** — JSON via structlog with request correlation IDs
- **OpenTelemetry** — Distributed tracing across services
- **Health probes** — `/health`, `/ready`, `/live` for container orchestrators

### Security

- **JWT authentication** — Access tokens (15 min) + refresh tokens (7 days)
- **RBAC** — Admin, operator, viewer roles
- **Rate limiting** — Tiered: 5/min (critical), 30/min (write), 60/min (read)
- **Security headers** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **Input validation** — Pydantic v2 on all endpoints

---

## Architecture

```
Client (React SPA / REST / WebSocket / CLI)
          │
          ▼
    ┌───────────┐
    │   Nginx   │  ← TLS termination, rate limit, gzip
    └─────┬─────┘
          ▼
   ┌──────────────┐
   │ FastAPI (API) │ ← 137 endpoints, JWT auth, middleware stack
   └──┬────────┬──┘
      │        │
      ▼        ▼
┌──────────┐ ┌───────┐
│PostgreSQL│ │ Redis │ ← Broker, cache, sessions
│  (data)  │ │       │
└──────────┘ └───────┘
      │
      ▼
┌──────────────────────┐
│ Prometheus + Grafana │ ← Metrics, dashboards, alerts
└──────────────────────┘
```

| Component     | Technology         | Version |
| ------------- | ------------------ | ------- |
| API           | FastAPI + Uvicorn  | 0.104.1 |
| Database      | PostgreSQL         | 15      |
| Broker/Cache  | Redis              | 7       |
| Frontend      | React + TypeScript | 19.2    |
| Build         | Vite               | 7.3     |
| Styling       | Tailwind CSS       | 4.1     |
| Monitoring    | Prometheus/Grafana | —       |
| Reverse Proxy | Nginx              | 1.25    |
| CI/CD         | GitHub Actions     | —       |

Full architecture docs: [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)

---

## API Overview

**137 endpoints** across **19 resource groups** — full OpenAPI spec at [docs/api/openapi.json](docs/api/openapi.json).

| Group           | Endpoints | Description                         |
| --------------- | --------- | ----------------------------------- |
| **Auth**        | 7         | Login, register, refresh, RBAC      |
| **Tasks**       | 16        | CRUD, retry, cancel, bulk, DLQ      |
| **Workers**     | 10        | Register, heartbeat, drain, pause   |
| **Campaigns**   | 13        | Lifecycle, recipients, templates    |
| **Templates**   | 7         | CRUD, preview, variable extraction  |
| **Workflows**   | 12        | DAG creation, chains, conditionals  |
| **Dashboard**   | 6         | Stats, widgets, activity feed       |
| **Analytics**   | 8         | Trends, patterns, summaries         |
| **Search**      | 8         | Full-text, filters, presets, export |
| **Alerts**      | 10        | CRUD, evaluate, acknowledge         |
| **Metrics**     | 5         | Prometheus, worker metrics          |
| **Resilience**  | 7         | Degradation, throughput, health     |
| **Chaos**       | 7         | Fault injection, experiment mgmt    |
| **Performance** | 6         | Profiling, DB tuning, baselines     |
| **Operations**  | 6         | Backup, restore, maintenance        |
| **Debug**       | 5         | Replay, compare, timeline           |
| **Health**      | 3         | Health, ready, live probes          |
| **WebSocket**   | 3         | Metrics, tasks, workers streams     |

Interactive documentation available at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc`.

---

## Manual Setup

### Prerequisites

- Python 3.10+ (3.13 recommended)
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev tools

# Configure environment
cp .env.example .env
# Edit .env with your database and Redis URLs

# Initialize database
python init_db.py

# Start API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

## Testing

```bash
# Backend tests (153 tests)
pytest                              # All tests
pytest --cov=src                    # With coverage
pytest tests/unit/                  # Unit only
pytest tests/integration/           # Integration only

# Frontend tests (293+ tests)
cd frontend
npm test                            # Jest + Testing Library
npm run test -- --coverage          # With coverage

# E2E tests (57+ tests)
cd frontend
npx playwright test                 # Playwright
npx playwright test --ui            # Interactive mode
```

| Suite     | Framework  | Count    | Coverage |
| --------- | ---------- | -------- | -------- |
| Backend   | pytest     | 153      | 80%+     |
| Frontend  | Jest + RTL | 293      | 80%+     |
| E2E       | Playwright | 57+      | —        |
| **Total** |            | **503+** |          |

---

## Docker

### Development

```bash
docker compose up -d --build
docker compose logs -f              # Stream logs
docker compose ps                   # Check status
docker compose down                 # Stop
```

### Production

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Includes Nginx reverse proxy, Prometheus, Grafana (port 3001), and cAdvisor.

---

## Configuration

All configuration via environment variables (`.env` file):

```ini
# Database
DATABASE_URL=postgresql://taskflow:taskflow@localhost:5432/taskflow

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Workers
WORKER_CAPACITY=5
WORKER_TIMEOUT_SECONDS=300
WORKER_MAX_RETRIES=5

# Email (optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=user
SMTP_PASSWORD=pass
```

---

## Documentation

| Topic               | Link                                                                                                           |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| Architecture        | [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)                                         |
| API Reference       | [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md)                                                         |
| OpenAPI Spec        | [docs/api/openapi.json](docs/api/openapi.json)                                                                 |
| Deployment Guide    | [docs/deployment/DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md)                                     |
| Docker Usage        | [docs/deployment/DOCKER_USAGE.md](docs/deployment/DOCKER_USAGE.md)                                             |
| Operational Runbook | [docs/RUNBOOK.md](docs/RUNBOOK.md)                                                                             |
| Monitoring Guide    | [docs/operations/MONITORING_GUIDE.md](docs/operations/MONITORING_GUIDE.md)                                     |
| Troubleshooting     | [docs/operations/TROUBLESHOOTING_AND_BEST_PRACTICES.md](docs/operations/TROUBLESHOOTING_AND_BEST_PRACTICES.md) |
| Changelog           | [docs/CHANGELOG.md](docs/CHANGELOG.md)                                                                         |
| Contributing        | [docs/development/CONTRIBUTING.md](docs/development/CONTRIBUTING.md)                                           |
| Code Style          | [docs/development/CODE_STYLE.md](docs/development/CODE_STYLE.md)                                               |
| Setup Guide         | [docs/setup/PROJECT_SETUP_SUMMARY.md](docs/setup/PROJECT_SETUP_SUMMARY.md)                                     |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the [Code Style Guide](docs/development/CODE_STYLE.md)
4. Add tests for new functionality
5. Ensure all tests pass (`pytest && cd frontend && npm test`)
6. Commit with conventional messages (`feat:`, `fix:`, `docs:`)
7. Submit a pull request

See [CONTRIBUTING.md](docs/development/CONTRIBUTING.md) for detailed guidelines.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
<sub>Built by the TaskFlow Team — v1.0.0</sub>
</div>
