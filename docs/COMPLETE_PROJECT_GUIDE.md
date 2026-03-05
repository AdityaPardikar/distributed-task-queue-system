    # TaskFlow — Complete Project Guide

> **How to run, deploy, understand, and interact with the Distributed Task Queue System**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture — How It Works](#2-architecture--how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Running Locally (Development)](#4-running-locally-development)
5. [Running with Docker Compose (Recommended)](#5-running-with-docker-compose-recommended)
6. [Production Deployment](#6-production-deployment)
7. [How to Interact as a User](#7-how-to-interact-as-a-user)
8. [API Reference Cheat Sheet](#8-api-reference-cheat-sheet)
9. [Monitoring & Observability](#9-monitoring--observability)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Project Overview

**TaskFlow** is a production-grade distributed task queue system with:

| Feature                    | Description                                                                  |
| -------------------------- | ---------------------------------------------------------------------------- |
| **Task Queue**             | Create, schedule, retry, cancel, and track async tasks with priority queues  |
| **Email Campaign Engine**  | Bulk email campaigns with templates, recipient management, rate limiting     |
| **Worker Management**      | Register workers, heartbeat monitoring, pause/resume/drain lifecycle         |
| **Workflow Orchestration** | DAG-based workflows, task dependencies, chains, templates                    |
| **Real-time Dashboard**    | React SPA with live WebSocket updates, charts, status badges                 |
| **Monitoring**             | Prometheus metrics, Grafana dashboards, OpenTelemetry tracing                |
| **Resilience**             | Circuit breakers, graceful degradation, dead letter queue, chaos engineering |
| **Security**               | JWT auth, role-based access, rate limiting, security headers                 |

### Tech Stack

```
Backend:   Python 3.11+ · FastAPI 0.104 · SQLAlchemy 2.0 · Celery 5.3
Frontend:  React 19 · TypeScript 5.9 · Vite 7 · Tailwind CSS 4 · Recharts
Database:  PostgreSQL 15 · Redis 7
Infra:     Docker · Nginx · Prometheus · Grafana · OpenTelemetry
Auth:      JWT (python-jose) · bcrypt · OAuth2
```

---

## 2. Architecture — How It Works

### High-Level Flow

```
                        ┌─────────────────┐
                        │   React SPA     │  (port 3000)
                        │   (Frontend)    │
                        └────────┬────────┘
                                 │ HTTP / WebSocket
                        ┌────────▼────────┐
                        │   Nginx Proxy   │  (port 80 — prod only)
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  FastAPI App    │  (port 8000)
                        │  (Backend API)  │
                        └──┬──────────┬───┘
                           │          │
                  ┌────────▼──┐  ┌────▼──────┐
                  │ PostgreSQL│  │   Redis    │
                  │  (Data)   │  │(Cache/Queue│
                  └───────────┘  └─────┬─────┘
                                       │
                                ┌──────▼──────┐
                                │   Celery    │
                                │  Workers    │
                                └─────────────┘
```

### How Each Component Works

1. **FastAPI Backend** (`src/api/main.py`)
   - Entry point: `run.py` starts `uvicorn` pointing to `src.api.main:app`
   - `create_app()` builds the FastAPI instance, adds middleware (CORS, rate limiting, security headers, request timing), and registers 17 route modules under `/api/v1/`
   - Global exception handlers return consistent JSON: `{"error": true, "detail": "...", "status_code": N}`
   - Settings loaded from `.env` via Pydantic (`src/config/settings.py`)

2. **PostgreSQL** — stores tasks, workers, campaigns, users, workflows, alerts
   - SQLAlchemy 2.0 ORM models in `src/models/`
   - Migrations via Alembic (`alembic.ini`)
   - `init_db.py` creates all tables from models (quick dev setup)

3. **Redis** — task queue broker, caching layer, rate-limit counters, pub/sub for WebSocket events

4. **Celery Workers** — pull tasks from Redis queues, execute them, report results back to PostgreSQL
   - Configurable capacity, timeouts, retries with exponential backoff
   - Dead Letter Queue (DLQ) for permanently failed tasks

5. **React Frontend** (`frontend/src/`)
   - Pages: Dashboard, Tasks, Workers, Campaigns, Templates, Analytics, Workflows, Alerts, Search
   - Uses `axios` for API calls, `react-router-dom` for routing, `recharts` for charts
   - WebSocket connection for live task/worker status updates
   - Responsive layout with mobile sidebar

6. **Nginx** (production) — reverse proxy, serves frontend static files, routes `/api/` to backend

---

## 3. Prerequisites

### For Local Development (without Docker)

| Tool       | Version | Install                                  |
| ---------- | ------- | ---------------------------------------- |
| Python     | 3.11+   | [python.org](https://python.org)         |
| Node.js    | 18+     | [nodejs.org](https://nodejs.org)         |
| PostgreSQL | 15+     | [postgresql.org](https://postgresql.org) |
| Redis      | 7+      | [redis.io](https://redis.io) or Docker   |
| Git        | 2.x     | [git-scm.com](https://git-scm.com)       |

### For Docker Deployment (recommended)

| Tool           | Version | Install                          |
| -------------- | ------- | -------------------------------- |
| Docker         | 24+     | [docker.com](https://docker.com) |
| Docker Compose | 2.x     | Bundled with Docker Desktop      |

---

## 4. Running Locally (Development)

### Step 1: Clone & Enter the Project

```powershell
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd distributed-task-queue-system
```

### Step 2: Create & Activate Virtual Environment

```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional: testing/linting tools
```

### Step 4: Configure Environment

```powershell
# Copy the template
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/Mac

# EDIT .env — at minimum, update these:
```

Key variables to set in `.env`:

```dotenv
# Generate a real key: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<your-random-64-char-string>

# Database — make sure this PostgreSQL instance is running
DATABASE_URL=postgresql://taskflow:taskflow@localhost:5432/taskflow

# Redis — must be running on this address
REDIS_URL=redis://localhost:6379/0

# Keep these for dev
APP_ENV=development
DEBUG=True
```

### Step 5: Start PostgreSQL & Redis

If you don't have them installed natively, use Docker for just the databases:

```powershell
docker run -d --name dtqs-postgres -e POSTGRES_USER=taskflow -e POSTGRES_PASSWORD=taskflow -e POSTGRES_DB=taskflow -p 5432:5432 postgres:15-alpine
docker run -d --name dtqs-redis -p 6379:6379 redis:7-alpine
```

### Step 6: Initialize the Database

```powershell
python init_db.py
```

This creates all tables — you should see `✅ All tables created successfully!`

### Step 7: (Optional) Seed Demo Data

```powershell
python scripts/seed_data.py
```

This populates the database with realistic demo users, tasks, workers, campaigns, and templates. Useful for testing the UI immediately.

### Step 8: Start the Backend API

```powershell
python run.py
```

The API starts at **http://localhost:8000**. You'll see:

- Swagger docs: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

### Step 9: Start the Frontend

Open a **new terminal**:

```powershell
cd frontend
npm install
npm run dev
```

The frontend starts at **http://localhost:5173** (Vite dev server).

### Step 10: (Optional) Start Celery Workers

Open another terminal:

```powershell
# Activate venv first
.\venv\Scripts\Activate.ps1
python -m src.core.worker
```

### Quick Setup (Windows — All-in-One)

Instead of steps 2-9, you can run:

```powershell
.\setup.bat
```

This automatically creates the venv, installs deps, copies `.env`, starts Docker services, and initializes the DB.

---

## 5. Running with Docker Compose (Recommended)

This starts **everything** in containers — no need to install Python, Node.js, or databases locally.

### Development Mode

```powershell
# 1. Configure environment
copy .env.example .env
# Edit .env with your settings (the defaults work for Docker)

# 2. Build & start all services
docker compose up --build -d

# 3. Initialize database
docker compose exec backend python init_db.py

# 4. (Optional) Seed demo data
docker compose exec backend python scripts/seed_data.py
```

| Service      | URL                        |
| ------------ | -------------------------- |
| Frontend     | http://localhost:3000      |
| Backend API  | http://localhost:5000      |
| Swagger Docs | http://localhost:5000/docs |
| PostgreSQL   | localhost:5432             |
| Redis        | localhost:6379             |

### Useful Commands

```powershell
# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f backend

# Restart a service
docker compose restart backend

# Stop everything
docker compose down

# Stop and delete volumes (⚠️ destroys data)
docker compose down -v

# Rebuild after code changes
docker compose up --build -d
```

---

## 6. Production Deployment

### Option A: Docker Compose (Single Server)

Best for: Small-to-medium deployments on a single VPS/VM.

#### 1. Prepare Server

```bash
# Ubuntu/Debian server
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker $USER    # logout/login required
```

#### 2. Clone & Configure

```bash
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd distributed-task-queue-system

cp .env.example .env
```

**Edit `.env` with production values:**

```dotenv
# ──── CRITICAL: change these ────
APP_ENV=production
DEBUG=False
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">

# Strong database password
DB_USER=taskflow
DB_PASSWORD=<strong-random-password>
DB_NAME=taskflow
DATABASE_URL=postgresql+psycopg2://taskflow:<password>@postgres:5432/taskflow

# Strong Redis password
REDIS_PASSWORD=<strong-random-password>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Restrict CORS to your actual domain
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Versions
BACKEND_VERSION=latest
FRONTEND_VERSION=latest

# Frontend API URL (via Nginx proxy)
VITE_API_URL=/api
VITE_WS_URL=/ws
```

#### 3. Build & Deploy

```bash
# Build images
docker compose -f docker-compose.prod.yml --env-file .env build

# Start services in the background
docker compose -f docker-compose.prod.yml --env-file .env up -d

# Initialize database
docker compose -f docker-compose.prod.yml exec backend python init_db.py

# Verify health
docker compose -f docker-compose.prod.yml ps
curl http://localhost/health
```

#### 4. SSL/TLS with Let's Encrypt (HTTPS)

For production HTTPS, add Certbot:

```bash
# Install certbot
sudo apt install certbot

# Get certificate (stop nginx temporarily or use webroot)
sudo certbot certonly --standalone -d yourdomain.com

# Add to nginx config or use a reverse proxy like Traefik/Caddy
```

Alternatively, use **Caddy** as a reverse proxy for automatic HTTPS:

```Caddyfile
yourdomain.com {
    reverse_proxy localhost:80
}
```

### Option B: Cloud Platform Deployment

#### AWS (EC2 + RDS + ElastiCache)

```
┌──────────────────────────────────────────────┐
│                   VPC                        │
│  ┌────────────┐  ┌────────┐  ┌───────────┐  │
│  │   EC2      │  │  RDS   │  │ElastiCache│  │
│  │(Docker     │──│(Postgres│──│  (Redis)  │  │
│  │ Compose)   │  │  15)   │  │           │  │
│  └────────────┘  └────────┘  └───────────┘  │
│       │                                      │
│  ┌────▼───┐                                  │
│  │  ALB   │  (Application Load Balancer)     │
│  └────────┘                                  │
└──────────────────────────────────────────────┘
```

1. Launch EC2 (t3.medium or larger), install Docker
2. Create RDS PostgreSQL 15 instance — update `DATABASE_URL`
3. Create ElastiCache Redis 7 cluster — update `REDIS_URL`
4. Configure Security Groups: ALB→EC2(80), EC2→RDS(5432), EC2→Redis(6379)
5. Set up ALB with HTTPS certificate from ACM
6. Deploy with `docker-compose.prod.yml` on EC2 (skip postgres/redis services since they're managed)

#### DigitalOcean (Droplet)

```bash
# Create droplet ($12/mo — 2 vCPU, 2GB RAM)
doctl compute droplet create taskflow --size s-2vcpu-2gb --image docker-20-04 --region nyc1

# SSH in and follow "Option A" steps above
```

#### Railway / Render / Fly.io (PaaS)

These platforms support Docker-based deployments with managed PostgreSQL and Redis:

```bash
# Example: Railway
railway init
railway add --plugin postgresql
railway add --plugin redis
railway up
```

### Production Checklist

| Item                                    | Status |
| --------------------------------------- | ------ |
| `SECRET_KEY` is a strong random value   | ☐      |
| `DB_PASSWORD` is strong and unique      | ☐      |
| `REDIS_PASSWORD` is set                 | ☐      |
| `DEBUG=False`                           | ☐      |
| `APP_ENV=production`                    | ☐      |
| CORS origins restricted to your domain  | ☐      |
| HTTPS/TLS configured                    | ☐      |
| Firewall rules: only 80/443 exposed     | ☐      |
| Database backups configured             | ☐      |
| Log rotation configured                 | ☐      |
| Health checks passing                   | ☐      |
| Monitoring (Prometheus/Grafana) enabled | ☐      |
| Resource limits set (CPU/memory)        | ☐      |

---

## 7. How to Interact as a User

### 7.1 The Web Dashboard (Frontend)

Open your browser to:

- **Dev**: http://localhost:5173 (Vite) or http://localhost:3000 (Docker)
- **Prod**: https://yourdomain.com

#### First-time Setup

1. **Register** — Click "Register" → Enter username, email, and password (min 8 chars)
2. **Login** — Enter your credentials → You receive a JWT token (stored automatically)
3. **Dashboard** — You land on the main dashboard showing real-time stats

#### Dashboard Pages

| Page          | What You Can Do                                                                                                         |
| ------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Dashboard** | View task counts by status, worker health, queue depth, hourly/daily charts                                             |
| **Tasks**     | Create new tasks, see all tasks with status badges, filter by status/priority, retry failed tasks, cancel running tasks |
| **Workers**   | View registered workers, see capacity vs active tasks, pause/resume/drain workers                                       |
| **Campaigns** | Create email campaigns, add recipients (single or bulk), set templates, launch campaigns, monitor progress              |
| **Templates** | Create Jinja2 email templates, preview with variables, edit/delete                                                      |
| **Analytics** | View completion rate trends, wait time trends, peak loads, failure patterns, retry success rates                        |
| **Workflows** | Create DAG-based workflows with task dependencies, visualize workflow graphs                                            |
| **Alerts**    | View active alerts by severity, acknowledge alerts, see alert history/stats                                             |
| **Search**    | Full-text search across tasks, apply filter presets, bulk actions (retry/cancel/boost), export CSV                      |

### 7.2 The REST API (Direct)

You can interact with the API directly using `curl`, Postman, or any HTTP client.

#### Authentication Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "mypassword123"}'

# 2. Login to get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=mypassword123"

# Response:
# {"access_token": "eyJhbG...", "refresh_token": "eyJhbG...", "token_type": "bearer"}

# 3. Use the token for all subsequent requests
export TOKEN="eyJhbG..."
```

#### Task Management

```bash
# Create a task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "Process Report",
    "task_function": "tasks.process_report",
    "task_args": {"report_id": 42},
    "priority": "HIGH",
    "max_retries": 3,
    "timeout_seconds": 120
  }'

# List all tasks (with filtering)
curl "http://localhost:8000/api/v1/tasks?status=PENDING&priority=HIGH&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Get a specific task
curl http://localhost:8000/api/v1/tasks/{task_id} \
  -H "Authorization: Bearer $TOKEN"

# Retry a failed task
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/retry \
  -H "Authorization: Bearer $TOKEN"

# Cancel a task
curl -X DELETE http://localhost:8000/api/v1/tasks/{task_id} \
  -H "Authorization: Bearer $TOKEN"
```

#### Worker Management

```bash
# List workers
curl http://localhost:8000/api/v1/workers \
  -H "Authorization: Bearer $TOKEN"

# Pause a worker
curl -X PATCH http://localhost:8000/api/v1/workers/{worker_id}/pause \
  -H "Authorization: Bearer $TOKEN"

# Resume a worker
curl -X PATCH http://localhost:8000/api/v1/workers/{worker_id}/resume \
  -H "Authorization: Bearer $TOKEN"

# Drain a worker (finish current tasks, accept no new ones)
curl -X POST http://localhost:8000/api/v1/workers/{worker_id}/drain \
  -H "Authorization: Bearer $TOKEN"
```

#### Email Campaigns

```bash
# Create a template
curl -X POST http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Welcome Email",
    "subject": "Welcome to {{company}}, {{name}}!",
    "body": "<h1>Hey {{name}}</h1><p>Thanks for joining {{company}}!</p>",
    "variables": ["name", "company"]
  }'

# Create a campaign
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 Welcome Campaign",
    "description": "Welcome new users from Q1",
    "template_id": "<template-uuid>",
    "rate_limit": 50
  }'

# Add recipients in bulk
curl -X POST http://localhost:8000/api/v1/campaigns/{campaign_id}/recipients/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"email": "user1@example.com", "variables": {"name": "User 1", "company": "Acme"}},
    {"email": "user2@example.com", "variables": {"name": "User 2", "company": "Acme"}}
  ]'

# Launch the campaign
curl -X POST http://localhost:8000/api/v1/campaigns/{campaign_id}/launch \
  -H "Authorization: Bearer $TOKEN"
```

#### Workflows (DAG)

```bash
# Create a workflow with dependencies
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ETL Pipeline",
    "tasks": [
      {"task_name": "Extract", "task_function": "etl.extract", "depends_on": []},
      {"task_name": "Transform", "task_function": "etl.transform", "depends_on": ["Extract"]},
      {"task_name": "Load", "task_function": "etl.load", "depends_on": ["Transform"]}
    ]
  }'
```

### 7.3 Interactive API Docs (Swagger)

The easiest way to explore and test all endpoints:

1. Open **http://localhost:8000/docs** in your browser
2. Click **Authorize** (🔓) at the top right
3. Login first via the `/api/v1/auth/login` endpoint
4. Paste your `access_token` into the Bearer Auth field
5. Now you can try any endpoint directly from the browser

### 7.4 WebSocket (Real-time Updates)

Connect to the WebSocket for live updates:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/tasks");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Task update:", data);
  // { type: "task_update", task_id: "...", status: "COMPLETED", ... }
};
```

### 7.5 Health & Status Checks (No Auth Required)

```bash
# Quick health check
curl http://localhost:8000/health
# {"status": "healthy", "checks": {"database": "ok", "redis": "ok"}, "uptime_seconds": 3600}

# Readiness (db + redis connectivity)
curl http://localhost:8000/ready

# Liveness (is the process alive)
curl http://localhost:8000/live

# App info
curl http://localhost:8000/info

# System status with health score
curl http://localhost:8000/system/status

# System resources (CPU, memory, disk)
curl http://localhost:8000/system/resources
```

---

## 8. API Reference Cheat Sheet

All endpoints are under `http://localhost:8000` (dev) or behind Nginx (prod).

| Category      | Method | Endpoint                                | Auth? |
| ------------- | ------ | --------------------------------------- | ----- |
| **Health**    | GET    | `/health`, `/ready`, `/live`, `/info`   | No    |
| **Auth**      | POST   | `/api/v1/auth/register`                 | No    |
| **Auth**      | POST   | `/api/v1/auth/login`                    | No    |
| **Auth**      | POST   | `/api/v1/auth/refresh`                  | Yes   |
| **Auth**      | GET    | `/api/v1/auth/me`                       | Yes   |
| **Tasks**     | POST   | `/api/v1/tasks`                         | Yes   |
| **Tasks**     | GET    | `/api/v1/tasks`                         | Yes   |
| **Tasks**     | GET    | `/api/v1/tasks/{id}`                    | Yes   |
| **Tasks**     | DELETE | `/api/v1/tasks/{id}`                    | Yes   |
| **Tasks**     | POST   | `/api/v1/tasks/{id}/retry`              | Yes   |
| **Tasks**     | GET    | `/api/v1/tasks/dlq`                     | Yes   |
| **Workers**   | GET    | `/api/v1/workers`                       | Yes   |
| **Workers**   | POST   | `/api/v1/workers`                       | Yes   |
| **Workers**   | PATCH  | `/api/v1/workers/{id}/pause`            | Yes   |
| **Workers**   | PATCH  | `/api/v1/workers/{id}/resume`           | Yes   |
| **Workers**   | POST   | `/api/v1/workers/{id}/drain`            | Yes   |
| **Campaigns** | POST   | `/api/v1/campaigns`                     | Yes   |
| **Campaigns** | GET    | `/api/v1/campaigns`                     | Yes   |
| **Campaigns** | POST   | `/api/v1/campaigns/{id}/launch`         | Yes   |
| **Templates** | POST   | `/api/v1/templates`                     | Yes   |
| **Templates** | GET    | `/api/v1/templates`                     | Yes   |
| **Workflows** | POST   | `/api/v1/workflows`                     | Yes   |
| **Analytics** | GET    | `/api/v1/analytics/performance-summary` | Yes   |
| **Search**    | GET    | `/api/v1/search/tasks?q=...`            | Yes   |
| **Alerts**    | GET    | `/api/v1/alerts`                        | Yes   |
| **Metrics**   | GET    | `/api/v1/metrics/prometheus`            | No    |
| **Dashboard** | GET    | `/api/v1/dashboard/stats`               | Yes   |
| **WebSocket** | WS     | `/ws/tasks`                             | Token |

Full OpenAPI specification: `docs/api/openapi.json`

### Rate Limits

| Tier     | Endpoints             | Limit      |
| -------- | --------------------- | ---------- |
| Critical | Auth (login/register) | 5 req/min  |
| Write    | POST/PUT/PATCH/DELETE | 30 req/min |
| Read     | GET                   | 60 req/min |

---

## 9. Monitoring & Observability

### Prometheus Metrics

Metrics endpoint (no auth): `http://localhost:8000/api/v1/metrics/prometheus`

Configure your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "taskflow"
    scrape_interval: 15s
    static_configs:
      - targets: ["backend:8000"]
    metrics_path: /api/v1/metrics/prometheus
```

### Grafana Dashboard

1. Add Prometheus as a data source (URL: `http://prometheus:9090`)
2. Import dashboards or build custom ones with these key metrics:
   - `taskflow_tasks_total` — task count by status
   - `taskflow_task_duration_seconds` — task execution time
   - `taskflow_workers_active` — number of active workers
   - `taskflow_queue_depth` — pending tasks in queue
   - `taskflow_http_requests_total` — API request count

### Structured Logging

All logs are JSON-formatted in production (`LOG_FORMAT=json`):

```json
{
  "timestamp": "2026-03-05T10:30:00Z",
  "level": "INFO",
  "message": "Task completed",
  "task_id": "abc-123",
  "duration_ms": 450,
  "request_id": "req-xyz"
}
```

---

## 10. Troubleshooting

### Common Issues

| Problem                           | Solution                                                                            |
| --------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------ |
| `Connection refused` on port 5432 | PostgreSQL isn't running — start with Docker or native install                      |
| `Connection refused` on port 6379 | Redis isn't running — `docker run -d --name dtqs-redis -p 6379:6379 redis:7-alpine` |
| `ModuleNotFoundError`             | Activate the venv: `.\venv\Scripts\Activate.ps1`                                    |
| Frontend shows "Network Error"    | Backend isn't running, or CORS origins don't include the frontend URL               |
| `401 Unauthorized`                | Token expired — call `/api/v1/auth/refresh` or log in again                         |
| Database tables don't exist       | Run `python init_db.py`                                                             |
| Port already in use               | Kill the existing process: `netstat -ano                                            | findstr :8000`then`taskkill /PID <pid> /F` |

### Verify Everything Is Working

```bash
# 1. Health check
curl http://localhost:8000/health
# → {"status": "healthy", ...}

# 2. Register + Login
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"testpass123"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=testpass123"
# → {"access_token": "...", ...}

# 3. Create a task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"task_name":"Test Task","task_function":"test.hello"}'
# → {"id": "...", "status": "PENDING", ...}

# 4. View dashboard
# Open http://localhost:5173 (or :3000) in browser
```

### Running Tests

```powershell
# Backend tests
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Frontend with coverage
npm run test:coverage
```

---

## Summary — Quick Start Cheat Sheet

```
# ── Fastest way to run everything (Docker) ──
copy .env.example .env
docker compose up --build -d
docker compose exec backend python init_db.py
docker compose exec backend python scripts/seed_data.py

# ── Open in browser ──
# Dashboard:   http://localhost:3000
# API Docs:    http://localhost:5000/docs
# Health:      http://localhost:5000/health
```

```
# ── Fastest way to run locally (no Docker for app) ──
python -m venv venv && .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # edit DATABASE_URL, REDIS_URL
python init_db.py               # create tables
python scripts/seed_data.py     # optional: demo data
python run.py                   # start API on :8000

cd frontend && npm install && npm run dev   # start UI on :5173
```
