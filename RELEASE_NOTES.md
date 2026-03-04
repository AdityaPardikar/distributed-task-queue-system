# Release Notes — TaskFlow v1.0.1

**Release Date:** 2026-03-04  
**Tag:** `v1.0.1`  
**Previous Release:** v1.0.0 (2026-03-02)

---

## Overview

TaskFlow v1.0.1 is the final polish release, completing Week 8 — the "Complete,
Polish & Ship" sprint. This release hardens backend error handling, improves
frontend UX with shared components and mobile responsiveness, and expands test
coverage across both stacks.

---

## What's New in v1.0.1

- **Structured error responses** — Global exception handlers return consistent JSON (`detail` + `code`)
- **Mobile-responsive sidebar** — Hamburger menu toggle with overlay for small viewports
- **Shared UI components** — StatusBadge, EmptyState, SkeletonLoader for consistent UX
- **Active navigation** — Sidebar highlights the current page
- **~40 new tests** — Component tests and backend edge-case coverage
- **543+ total automated tests** (up from 503+)

---

## Highlights

- **137 REST API endpoints** across 19 resource groups
- **543+ automated tests** (backend, frontend, E2E)
- **Real-time dashboard** with WebSocket-powered live updates
- **Production monitoring** with Prometheus, Grafana, and structured logging
- **Security hardened** with JWT auth, RBAC, rate limiting, security headers
- **Fully containerized** with Docker Compose (dev + prod configurations)
- **CI/CD ready** with GitHub Actions pipelines

---

## Features

### Core Task Queue

- Priority-based task queuing (CRITICAL / HIGH / MEDIUM / LOW)
- Automatic retries with exponential backoff and jitter
- DAG-based task dependencies with topological resolution
- Cron-based task scheduling
- Dead letter queue with 30-day retention and replay
- Workflow engine — sequential chains, parallel fan-out, conditional branching

### Email Campaign Engine

- Campaign CRUD with full lifecycle management (create, launch, pause, resume, cancel)
- Jinja2 template engine with variable extraction and preview rendering
- Recipient management with bulk operations and status tracking
- Per-campaign rate limiting

### API (FastAPI)

- 137 endpoints organized into 19 tagged groups
- JWT authentication with access/refresh token flow
- Role-based access control (admin, operator, viewer)
- Tiered rate limiting (5/min critical, 30/min write, 60/min read)
- OpenAPI 3.1 specification with full schema documentation
- WebSocket endpoints for real-time metrics, task, and worker feeds
- Health, readiness, and liveness probes

### Frontend Dashboard (React 19)

- Task management — list, search, filter, retry, cancel, export
- Worker monitoring — status grid, actions, heartbeat tracking
- Campaign views — progress tracking, recipient lists, launch controls
- Analytics — trends, patterns, summary charts
- Alert management — severity-based alerts, acknowledge, silence
- Workflow visualization — DAG diagrams, chain/parallel views
- Settings — tabbed admin panel
- Command palette — keyboard-driven navigation (Ctrl+K)
- Notification center — activity feed, toast notifications

### Monitoring & Observability

- Prometheus metrics with recording rules and SLO-based alerts
- 3 pre-built Grafana dashboards (tasks, workers, system health)
- Structured JSON logging via structlog with request correlation IDs
- OpenTelemetry distributed tracing
- cAdvisor container metrics

### Security

- Security headers middleware (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- Bcrypt password hashing
- JWT tokens with configurable expiry
- CORS configuration with origin whitelist
- SQL injection protection via SQLAlchemy ORM
- Environment-based secrets management

### Infrastructure

- Docker Compose configurations (development + production)
- Nginx reverse proxy with TLS termination, gzip, static caching
- Multi-stage Docker builds for minimal image sizes
- GitHub Actions CI/CD (lint, test, build, deploy)
- Dependabot for automated dependency updates
- Pre-commit hooks (black, isort, flake8, mypy)
- Makefile with dev, test, build, deploy targets

---

## Testing

| Suite         | Framework              | Count    |
| ------------- | ---------------------- | -------- |
| Backend unit  | pytest                 | 153      |
| Frontend unit | Jest + Testing Library | 293      |
| E2E           | Playwright             | 57+      |
| Smoke         | httpx (custom)         | 16       |
| **Total**     |                        | **519+** |

---

## Documentation

| Document                              | Description                               |
| ------------------------------------- | ----------------------------------------- |
| `README.md`                           | Project overview and quick start          |
| `docs/api/openapi.json`               | OpenAPI 3.1 specification (137 endpoints) |
| `docs/api/API_REFERENCE.md`           | API reference guide                       |
| `docs/architecture/ARCHITECTURE.md`   | System architecture with diagrams         |
| `docs/RUNBOOK.md`                     | Operational runbook                       |
| `docs/CHANGELOG.md`                   | Complete changelog                        |
| `docs/PERFORMANCE_BASELINE.md`        | Performance targets and baselines         |
| `docs/deployment/DEPLOYMENT_GUIDE.md` | Deployment instructions                   |
| `docs/deployment/DOCKER_USAGE.md`     | Docker usage guide                        |
| `docs/operations/MONITORING_GUIDE.md` | Monitoring setup                          |
| `docs/development/CODE_STYLE.md`      | Coding standards and review checklist     |
| `docs/development/CONTRIBUTING.md`    | Contribution guidelines                   |

---

## Tech Stack

| Layer          | Technology                                     |
| -------------- | ---------------------------------------------- |
| Language       | Python 3.13                                    |
| API            | FastAPI 0.104.1, Uvicorn 0.24.0                |
| Database       | PostgreSQL 15, SQLAlchemy 2.0.23, Alembic 1.13 |
| Cache / Broker | Redis 7                                        |
| Frontend       | React 19.2, TypeScript 5.9, Vite 7.3           |
| Styling        | Tailwind CSS 4.1                               |
| Charts         | Recharts 3.7                                   |
| Monitoring     | Prometheus, Grafana 10, cAdvisor               |
| Proxy          | Nginx 1.25                                     |
| CI/CD          | GitHub Actions                                 |
| E2E Testing    | Playwright 1.52                                |

---

## Upgrade Notes

This is the initial production release. No upgrade path required.

---

## Known Limitations

- Kubernetes manifests are not included (Docker Compose only)
- GraphQL API is not yet available
- Multi-tenancy is not supported in this release
- Email sending requires external SMTP configuration

---

## What's Next

Potential areas for v1.1.0+:

- Kubernetes deployment manifests with Helm charts
- GraphQL API layer
- Advanced analytics with time-series storage
- Webhook integration for task lifecycle events
- Multi-tenancy support
- Mobile companion app

---

## Contributors

TaskFlow Team

## License

MIT License
