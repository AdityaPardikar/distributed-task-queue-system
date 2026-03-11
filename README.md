<div align="center">

<img src="https://img.icons8.com/3d-fluency/94/workflow.png" width="80" alt="TaskFlow Logo"/>

# TaskFlow

### ⚡ Production-Grade Distributed Task Queue System

A high-performance, scalable task queue with an integrated email campaign engine,<br/>
real-time dashboard, and full observability stack — built with FastAPI and React.

<br/>

[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Tailwind](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)

[![Stars](https://img.shields.io/github/stars/AdityaPardikar/distributed-task-queue-system?style=for-the-badge&color=f59e0b)](https://github.com/AdityaPardikar/distributed-task-queue-system/stargazers)
[![Forks](https://img.shields.io/github/forks/AdityaPardikar/distributed-task-queue-system?style=for-the-badge&color=8b5cf6)](https://github.com/AdityaPardikar/distributed-task-queue-system/network)
[![Last Commit](https://img.shields.io/github/last-commit/AdityaPardikar/distributed-task-queue-system?style=for-the-badge&color=6366f1)](https://github.com/AdityaPardikar/distributed-task-queue-system/commits)
[![Issues](https://img.shields.io/github/issues/AdityaPardikar/distributed-task-queue-system?style=for-the-badge&color=ef4444)](https://github.com/AdityaPardikar/distributed-task-queue-system/issues)

<br/>

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API](#-api-reference) · [Contributing](#-contributing)

</div>

<br/>

---

<br/>

## 📖 Overview

**TaskFlow** is a full-stack distributed task queue system designed for reliability, observability, and scale. It combines a robust Python backend with a modern React dashboard to provide:

- **Intelligent task orchestration** with DAG-based dependencies, priority queues, and automatic retries
- **Email campaign engine** with template management, recipient tracking, and rate limiting
- **Real-time monitoring** via WebSockets, Prometheus metrics, and structured logging
- **Enterprise-grade security** with JWT authentication, role-based access control, and tiered rate limiting

> [!NOTE]
> TaskFlow ships with **137 API endpoints** across 19 resource groups, a complete React SPA with 16+ pages, and full Docker support for one-command deployment.

<br/>

---

<br/>

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔄 Task Queue Engine

- Priority queues — `CRITICAL` / `HIGH` / `MEDIUM` / `LOW`
- Automatic retries with exponential backoff & jitter
- DAG-based task dependency resolution
- Cron-based scheduled task execution
- Dead letter queue with 30-day retention & replay
- Workflow chains, parallel fan-out, conditional branching

</td>
<td width="50%">

### 📧 Email Campaign Engine

- Full campaign lifecycle — create, schedule, launch, pause, resume, cancel
- Jinja2 template engine with variable extraction & preview
- Bulk recipient import with deduplication
- Per-campaign send rate controls
- Delivery status tracking & analytics

</td>
</tr>
<tr>
<td width="50%">

### 📊 Real-Time Dashboard

- React 19 SPA with TypeScript & Tailwind CSS 4
- WebSocket-powered live metrics & activity feeds
- Task management — search, filter, retry, cancel, export
- Campaign progress tracking & recipient stats
- Alert management with severity levels
- Command palette for keyboard-driven navigation (`Ctrl+K`)

</td>
<td width="50%">

### 🔭 Observability & Security

- Prometheus metrics — throughput, latency histograms, queue depth
- Structured JSON logging via `structlog` with correlation IDs
- OpenTelemetry distributed tracing
- Health probes — `/health`, `/ready`, `/live`
- JWT auth with access & refresh tokens
- RBAC — admin, operator, viewer roles
- Security headers — CSP, HSTS, X-Frame-Options

</td>
</tr>
</table>

<br/>

---

<br/>

## 🛠️ Tech Stack

<div align="center">

|       Layer       | Technology                                                                                                                                                                                                                                                                                                                                                                                                                             | Purpose                         |
| :---------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------ |
|  🖥️ **Backend**   | ![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=flat-square&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)                                                                                                        | API server, ORM, business logic |
|  🎨 **Frontend**  | ![React](https://img.shields.io/badge/React_19-61DAFB?style=flat-square&logo=react&logoColor=black) ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white) ![Tailwind](https://img.shields.io/badge/Tailwind_CSS_4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white) ![Vite](https://img.shields.io/badge/Vite_7-646CFF?style=flat-square&logo=vite&logoColor=white) | SPA dashboard, real-time UI     |
|  🗄️ **Database**  | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL_15-4169E1?style=flat-square&logo=postgresql&logoColor=white)                                                                                                                                                                                                                                                                                                                     | Primary data store              |
|   ⚡ **Broker**   | ![Redis](https://img.shields.io/badge/Redis_7-DC382D?style=flat-square&logo=redis&logoColor=white)                                                                                                                                                                                                                                                                                                                                     | Message broker, cache, sessions |
| 📈 **Monitoring** | ![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat-square&logo=prometheus&logoColor=white) ![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-7B5EA7?style=flat-square&logo=opentelemetry&logoColor=white)                                                                                                                                                                                               | Metrics, tracing                |
|   🚀 **DevOps**   | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)                                                                                                                                                                                                         | Containerization, CI/CD         |

</div>

<br/>

---

<br/>

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Client["🖥️ Client Layer"]
        SPA["React SPA<br/><i>Port 5173</i>"]
        WS["WebSocket"]
    end

    subgraph API["⚙️ API Layer"]
        FAST["FastAPI Server<br/><i>Port 8000</i>"]
        AUTH["JWT Auth<br/>+ RBAC"]
        MW["Middleware Stack<br/><i>Rate Limit · CORS · Headers</i>"]
    end

    subgraph Data["🗄️ Data Layer"]
        PG["PostgreSQL<br/><i>Primary Store</i>"]
        RD["Redis<br/><i>Broker · Cache · Sessions</i>"]
    end

    subgraph Observe["📈 Observability"]
        PROM["Prometheus"]
        OTEL["OpenTelemetry"]
        LOG["Structured Logging"]
    end

    SPA -->|REST API| FAST
    SPA -.->|Live Feeds| WS
    WS --> FAST
    FAST --> AUTH
    AUTH --> MW
    MW --> PG
    MW --> RD
    FAST --> PROM
    FAST --> OTEL
    FAST --> LOG

    style Client fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    style API fill:#e0e7ff,stroke:#6366f1,color:#312e81
    style Data fill:#dcfce7,stroke:#22c55e,color:#14532d
    style Observe fill:#fef3c7,stroke:#f59e0b,color:#78350f
```

<br/>

---

<br/>

## 🚀 Quick Start

### Prerequisites

| Tool       | Version                  |        Required        |
| :--------- | :----------------------- | :--------------------: |
| Python     | 3.10+ (3.13 recommended) |           ✅           |
| Node.js    | 18+                      |           ✅           |
| PostgreSQL | 15+                      | ✅ (or SQLite for dev) |
| Redis      | 7+                       |           ✅           |
| Docker     | 24+                      |        Optional        |

### Option 1 — Docker (Recommended)

```bash
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd distributed-task-queue-system
docker compose up -d --build
```

### Option 2 — Manual Setup

<details>
<summary><b>🔧 Backend Setup</b></summary>
<br/>

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and Redis URLs

# Initialize the database
python init_db.py

# Start the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

</details>

<details>
<summary><b>🎨 Frontend Setup</b></summary>
<br/>

```bash
cd frontend
npm install
npm run dev
```

</details>

<br/>

> [!TIP]
> After startup, open the **Dashboard** at `http://localhost:5173` and the **Swagger UI** at `http://localhost:8000/docs`.

<br/>

---

<br/>

## 📡 API Reference

TaskFlow exposes **137 endpoints** across **19 resource groups** with full interactive documentation via Swagger UI.

<details>
<summary><b>View All Endpoint Groups</b></summary>
<br/>

| Group            | Endpoints | Description                               |
| :--------------- | :-------: | :---------------------------------------- |
| 🔐 **Auth**      |     7     | Login, register, refresh tokens, RBAC     |
| 📋 **Tasks**     |    16     | CRUD, retry, cancel, bulk operations, DLQ |
| 👷 **Workers**   |    10     | Register, heartbeat, drain, pause         |
| 📧 **Campaigns** |    13     | Full lifecycle, recipients, templates     |
| 📝 **Templates** |     7     | CRUD, preview, variable extraction        |
| 🔀 **Workflows** |    12     | DAG creation, chains, conditionals        |
| 📊 **Dashboard** |     6     | Stats, widgets, activity feed             |
| 📈 **Analytics** |     8     | Trends, patterns, summaries               |
| 🔔 **Alerts**    |    10     | CRUD, evaluate, acknowledge               |
| 💚 **Health**    |     3     | Health, ready, live probes                |
| 🔌 **WebSocket** |     3     | Real-time metrics, tasks, workers         |

</details>

<br/>

---

<br/>

## 📁 Project Structure

```
taskflow/
├── 📂 src/                         # Backend source code
│   ├── 📂 api/                     #   FastAPI routes, middleware, schemas
│   ├── 📂 core/                    #   Task engine, scheduler, workflows
│   ├── 📂 models/                  #   SQLAlchemy database models
│   ├── 📂 services/                #   Business logic layer
│   ├── 📂 db/                      #   Database sessions & migrations
│   ├── 📂 cache/                   #   Redis caching layer
│   ├── 📂 config/                  #   Settings & configuration
│   ├── 📂 monitoring/              #   Prometheus metrics
│   ├── 📂 observability/           #   Logging & OpenTelemetry tracing
│   ├── 📂 resilience/              #   Circuit breakers, chaos engineering
│   └── 📂 performance/             #   Profiling & query optimization
│
├── 📂 frontend/                    # React TypeScript SPA
│   └── 📂 src/
│       ├── 📂 components/          #   Reusable UI components
│       ├── 📂 pages/               #   Page-level components
│       ├── 📂 context/             #   React context providers
│       ├── 📂 hooks/               #   Custom React hooks
│       ├── 📂 services/            #   API client & utilities
│       └── 📂 styles/              #   Global styles & design tokens
│
├── 📂 tests/                       # Test suite
│   ├── 📂 unit/                    #   Unit tests
│   ├── 📂 integration/             #   Integration tests
│   └── 📂 load/                    #   Load tests (Locust)
│
├── 📂 monitoring/                  # Prometheus configuration
├── 📂 .github/workflows/           # CI/CD pipelines
├── 📄 docker-compose.yml           # Development stack
├── 📄 Dockerfile.backend           # Backend container
├── 📄 Dockerfile.frontend          # Frontend container
├── 📄 requirements.txt             # Python dependencies
└── 📄 pyproject.toml               # Project metadata
```

<br/>

---

<br/>

## ⚙️ Configuration

All settings are managed through environment variables. Copy `.env.example` to `.env` and customize:

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
```

> [!IMPORTANT]
> Always change `SECRET_KEY` before deploying to production. See `.env.example` for the full list of configurable options.

<br/>

---

<br/>

## 🧪 Testing

```bash
# Run backend tests
pytest

# Run with coverage report
pytest --cov=src

# Run frontend tests
cd frontend && npm test
```

<br/>

---

<br/>

## 🗺️ Roadmap

- [ ] Grafana dashboard templates
- [ ] Worker auto-scaling based on queue depth
- [ ] Plugin system for custom task handlers
- [ ] Webhook notifications for task events
- [ ] Multi-tenant workspace support
- [ ] CLI tool for task management

<br/>

---

<br/>

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch — `git checkout -b feature/amazing-feature`
3. **Add tests** for new functionality
4. **Ensure** all tests pass — `pytest && cd frontend && npm test`
5. **Commit** with conventional messages — `feat:`, `fix:`, `docs:`
6. **Submit** a pull request

<br/>

---

<br/>

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

<br/>

---

<div align="center">

<br/>

**Built with ❤️ by [Aditya Pardikar](https://github.com/AdityaPardikar)**

⭐ Star this repo if you found it useful!

<br/>

</div>
