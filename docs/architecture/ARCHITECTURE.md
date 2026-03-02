# Architecture — TaskFlow Distributed Task Queue System

> **Version:** 1.0.0 | **Last Updated:** 2026-03-02

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  ┌────────────┐  │
│  │ React SPA    │  │ REST Clients │  │ WebSocket │  │ CLI (Click)│  │
│  │ (Vite, TS)   │  │ (httpx, curl)│  │ Clients   │  │            │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  └─────┬──────┘  │
└─────────┼──────────────────┼───────────────┼───────────────┼─────────┘
          │ HTTPS            │ HTTPS         │ WSS           │ HTTPS
          ▼                  ▼               ▼               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       REVERSE PROXY (Nginx)                          │
│  Port 80/443 — TLS termination, gzip, static caching, rate limit    │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  API Server  │  │  API Server  │  │  API Server  │
│  (FastAPI)   │  │  (replica)   │  │  (replica)   │
│  Port 8000   │  │  Port 8001   │  │  Port 8002   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     SHARED INFRASTRUCTURE                            │
│                                                                      │
│  ┌──────────────────┐         ┌──────────────────┐                   │
│  │   PostgreSQL 15   │         │     Redis 7       │                  │
│  │   (Primary DB)    │         │  (Broker + Cache)  │                 │
│  │   Port 5432       │         │  Port 6379         │                 │
│  │                   │         │                    │                  │
│  │  Tables:          │         │  Structures:       │                 │
│  │  • tasks          │         │  • Priority queues  │                │
│  │  • workers        │         │  • Task metadata    │                │
│  │  • campaigns      │         │  • Worker registry  │                │
│  │  • recipients     │         │  • Rate limit keys  │                │
│  │  • templates      │         │  • Cache entries    │                │
│  │  • users          │         │  • Session data     │                │
│  └──────────────────┘         └──────────────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY STACK                               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐                   │
│  │  Prometheus   │  │   Grafana    │  │  cAdvisor  │                  │
│  │  Port 9090    │  │  Port 3001   │  │  Port 8080 │                  │
│  │  (scraping)   │  │ (dashboards) │  │ (container)│                  │
│  └──────────────┘  └──────────────┘  └───────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### API Server (FastAPI)

The API server is the central gateway, handling all HTTP and WebSocket requests.

```
src/api/
├── main.py                  # App factory, middleware stack, router registration
├── middleware.py             # Request ID injection, timing middleware
├── security.py              # SecurityHeaders middleware, tiered rate limiting
├── schemas.py               # Shared Pydantic schemas
├── auth_deps/               # Authentication dependency injection
└── routes/
    ├── auth.py              # /api/v1/auth/*         — JWT auth, user management
    ├── tasks.py             # /api/v1/tasks/*        — Task CRUD, DLQ, dependencies
    ├── workers.py           # /api/v1/workers/*      — Worker lifecycle management
    ├── campaigns.py         # /api/v1/campaigns/*    — Campaign CRUD, launch, recipients
    ├── templates.py         # /api/v1/templates/*    — Email template CRUD, preview
    ├── dashboard.py         # /api/v1/dashboard/*    — Dashboard stats & widgets
    ├── analytics.py         # /api/v1/analytics/*    — Trends, patterns, summaries
    ├── search.py            # /api/v1/search/*       — Full-text search, presets, export
    ├── workflows.py         # /api/v1/workflows/*    — Workflow creation, batch tasks
    ├── advanced_workflows.py# /api/v1/workflows/advanced/* — DAG, templates, chains
    ├── alerts.py            # /api/v1/alerts/*       — Alert management, evaluation
    ├── metrics.py           # /api/v1/metrics/*      — Prometheus metrics, worker metrics
    ├── resilience.py        # /api/v1/resilience/*   — Degradation, throughput, health
    ├── chaos.py             # /api/v1/chaos/*        — Chaos experiments, DLQ
    ├── performance.py       # /api/v1/performance/*  — Profiling, DB tuning
    ├── operations.py        # /api/v1/operations/*   — Backup, maintenance, config
    ├── debug.py             # /api/v1/tasks/*/debug  — Replay, compare, timeline
    ├── health.py            # /health, /ready, /live — Health probes
    └── websocket.py         # /ws/metrics, /ws/tasks, /ws/workers
```

**Middleware Stack** (execution order, outermost first):

1. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options
2. `TrustedHostMiddleware` — Host header validation
3. `CORSMiddleware` — Cross-origin request handling
4. `add_request_id` — UUID request tracing
5. `request_timing_middleware` — X-Response-Time header
6. `tiered_rate_limit_middleware` — Per-tier rate limiting
7. `performance_tracking_middleware` — Profiler recording

### Core Engine

```
src/core/
├── broker.py                # Redis broker — priority queues, task enqueue/dequeue
├── worker_controller.py     # Worker lifecycle — register, heartbeat, drain
├── scheduler.py             # Cron-based task scheduling
├── retry.py                 # Exponential backoff with jitter
├── dependency_resolver.py   # DAG dependency resolution
├── event_bus.py             # Pub/sub event system for real-time updates
├── workflow_engine.py       # Basic workflow orchestration
├── advanced_workflow.py     # Conditional branching, typed dependencies
└── serializer.py            # JSON/Pickle task serialization
```

### Services Layer

```
src/services/
├── auth_service.py          # User creation, password hashing, token management
├── task_service.py          # Task business logic, status transitions
├── worker_service.py        # Worker management, capacity tracking
├── campaign_launcher.py     # Campaign launching, recipient iteration
├── email_template_engine.py # Jinja2 rendering, variable extraction
├── task_search.py           # Full-text search, filter presets
└── task_debugger.py         # Debug mode, execution logs, task replay
```

### Frontend (React SPA)

```
frontend/src/
├── App.tsx                  # Route definitions, layout wrapper
├── main.tsx                 # React 19 entry point
├── context/
│   ├── AuthContext.tsx       # JWT auth state, login/logout/refresh
│   └── NotificationContext.tsx # Toast notifications, activity feed
├── components/
│   ├── Layout.tsx            # Sidebar navigation, topbar, command palette
│   ├── ProtectedRoute.tsx    # Auth guard — redirects to /login
│   ├── DashboardPage.tsx     # Metrics cards, charts, worker health
│   ├── TasksPage.tsx         # Task table, filters, pagination, export
│   ├── WorkersPage.tsx       # Worker grid, status, actions
│   ├── CampaignListPage.tsx  # Campaign table, launch/pause actions
│   ├── CreateCampaignPage.tsx# Campaign creation form
│   ├── CampaignDetailPage.tsx# Campaign progress, recipient list
│   ├── TemplateListPage.tsx  # Template management
│   ├── AlertsPage.tsx        # Alert list, severity, acknowledge
│   ├── MonitoringPage.tsx    # System resource monitoring
│   ├── WorkflowsPage.tsx     # DAG visualization, workflow management
│   ├── SettingsPage.tsx      # Admin settings (tabbed)
│   ├── AnalyticsPage.tsx     # Charts, trends, analytics
│   ├── SearchResultsPage.tsx # Search results with filters
│   ├── LoginPage.tsx         # Login form
│   └── RegisterForm.tsx      # Registration form
└── hooks/
    ├── useApi.ts             # HTTP client with auth headers
    └── useTaskEvents.ts      # WebSocket subscription hooks
```

---

## Data Flow

### Task Lifecycle

```
1. Client POST /api/v1/tasks
       │
       ▼
2. API validates request (Pydantic)
       │
       ▼
3. Task record INSERT → PostgreSQL (status: PENDING)
       │
       ▼
4. Task enqueued → Redis priority queue
       │ (status: QUEUED)
       ▼
5. Worker BLPOP from Redis queue
       │ (status: RUNNING)
       ▼
6. Worker executes task function
       │
       ├── Success ──► PostgreSQL UPDATE (status: COMPLETED, result stored)
       │                    │
       │                    ▼
       │               Event bus → WebSocket → Client notified
       │
       └── Failure ──► Retry? ──► Yes ──► Redis re-enqueue (status: RETRYING)
                        │                      │
                        │                      ▼
                        │                 Back to step 5 (with backoff)
                        │
                        └──── No ──► Dead Letter Queue (status: FAILED)
                                          │
                                          ▼
                                     Admin reviews via DLQ API
```

### Authentication Flow

```
1. POST /api/v1/auth/login  { username, password }
       │
       ▼
2. Verify password (bcrypt hash comparison)
       │
       ▼
3. Generate JWT access token (15 min) + refresh token (7 days)
       │
       ▼
4. Client stores tokens in localStorage
       │
       ▼
5. Subsequent requests: Authorization: Bearer <access_token>
       │
       ▼
6. Token expired? → POST /api/v1/auth/refresh with refresh_token
       │
       ▼
7. New access token issued
```

### WebSocket Real-Time Pipeline

```
Client ──WSS──► Nginx ──► FastAPI WebSocket handler
                                    │
                                    ▼
                              ConnectionManager
                              (per-channel subscriptions)
                                    │
                          ┌─────────┼─────────┐
                          ▼         ▼         ▼
                     /ws/metrics /ws/tasks /ws/workers
                          │         │         │
                          ▼         ▼         ▼
                      Event Bus (pub/sub pattern)
                          │
                    ┌─────┼─────┐
                    ▼     ▼     ▼
               Task      Worker    Alert
              Events    Events   Events
```

---

## Deployment Topology

### Development

```yaml
# docker-compose.yml
services:
  postgres: # Port 5432
  redis: # Port 6379
  backend: # Port 8000 (uvicorn --reload)
  frontend: # Port 5173 (vite dev)
```

### Production

```yaml
# docker-compose.prod.yml
services:
  postgres: # Internal only, resource limits
  redis: # Internal only, maxmemory policy
  api: # Port 8000, gunicorn + uvicorn workers
  frontend: # Static build served by Nginx
  nginx: # Port 80/443, reverse proxy, TLS
  prometheus: # Port 9090, metrics scraping
  grafana: # Port 3001, dashboards
  cadvisor: # Port 8080, container metrics
```

### Security Layers

| Layer            | Protection                                              |
| ---------------- | ------------------------------------------------------- |
| Nginx            | TLS termination, request size limits, gzip              |
| Rate Limiting    | Tiered: 5/min (critical), 30/min (write), 60/min (read) |
| Authentication   | JWT with 15-min expiry, bcrypt password hashing         |
| Authorization    | RBAC — admin, operator, viewer roles                    |
| CORS             | Configurable origin whitelist                           |
| Headers          | CSP, HSTS, X-Frame-Options, X-Content-Type-Options      |
| Input Validation | Pydantic v2 models on all endpoints                     |
| SQL Injection    | SQLAlchemy ORM (parameterized queries)                  |
| Secrets          | Environment variables, never in code                    |

---

## Technology Stack

| Category           | Technology                         | Version |
| ------------------ | ---------------------------------- | ------- |
| Language           | Python                             | 3.13    |
| API Framework      | FastAPI                            | 0.104.1 |
| ASGI Server        | Uvicorn                            | 0.24.0  |
| ORM                | SQLAlchemy                         | 2.0.23  |
| Migrations         | Alembic                            | 1.13.1  |
| Validation         | Pydantic                           | 2.5.0   |
| Database           | PostgreSQL                         | 15      |
| Cache / Broker     | Redis                              | 7       |
| Frontend           | React                              | 19.2    |
| Type System        | TypeScript                         | 5.9     |
| Build Tool         | Vite                               | 7.3     |
| Styling            | Tailwind CSS                       | 4.1     |
| Charts             | Recharts                           | 3.7     |
| Auth               | python-jose (JWT), bcrypt, passlib | —       |
| Email              | aiosmtplib, Jinja2                 | —       |
| Monitoring         | Prometheus, Grafana, OpenTelemetry | —       |
| Logging            | structlog (JSON)                   | 23.3    |
| Testing (Backend)  | pytest, pytest-cov                 | 7.4     |
| Testing (Frontend) | Jest, Testing Library              | 30.2    |
| Testing (E2E)      | Playwright                         | 1.52    |
| CI/CD              | GitHub Actions                     | —       |
| Containerization   | Docker, Docker Compose             | —       |
| Reverse Proxy      | Nginx                              | 1.25    |
