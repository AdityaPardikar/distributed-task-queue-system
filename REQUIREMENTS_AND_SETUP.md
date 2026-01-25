# Requirements and Setup Guide - Distributed Task Queue System

## Complete Requirements Checklist

This document outlines all external applications, dependencies, and system requirements needed to run the Distributed Task Queue System.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Programming Languages & Runtimes](#programming-languages--runtimes)
3. [External Applications & Services](#external-applications--services)
4. [Python Dependencies](#python-dependencies)
5. [Database Setup](#database-setup)
6. [Installation Steps](#installation-steps)
7. [Configuration Files](#configuration-files)

---

## System Requirements

### Hardware

- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Disk Space**: 20GB for development, 100GB+ for production
- **Network**: Internet connection for downloading dependencies

### Operating Systems

- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 9+
- **macOS**: 10.14+ (Intel or Apple Silicon)
- **Windows**: Windows 10/11 with WSL2 (recommended) or native

### Network Requirements

- Port 5432: PostgreSQL database
- Port 6379: Redis cache
- Port 8000: API server
- Port 9090: Prometheus metrics
- Port 3001: Grafana dashboard
- Port 4318: OpenTelemetry OTLP exporter
- Port 16686: Jaeger tracing UI

---

## Programming Languages & Runtimes

### Python

- **Version**: Python 3.9 or later
- **Download**: https://www.python.org/downloads/
- **Installation**:

  ```bash
  # Linux/macOS
  python3 --version  # Verify installation

  # Windows
  python --version
  ```

- **Virtual Environment**: Built-in `venv` module
  ```bash
  python3 -m venv venv
  source venv/bin/activate  # macOS/Linux
  venv\Scripts\activate     # Windows
  ```

### Node.js (Optional - for frontend/dashboard)

- **Version**: 16+ (if using Node-based tools)
- **Download**: https://nodejs.org/
- **Not required** for backend server

---

## External Applications & Services

### 1. PostgreSQL (Required - Database)

- **Version**: 12.0 or later
- **Download**: https://www.postgresql.org/download/
- **Purpose**: Primary relational database for tasks, workers, schedules
- **Installation**:

  ```bash
  # macOS (Homebrew)
  brew install postgresql@15

  # Ubuntu/Debian
  sudo apt-get install postgresql postgresql-contrib

  # Windows
  # Download installer from postgresql.org

  # Or use Docker (recommended)
  docker pull postgres:15-alpine
  ```

- **Configuration**:
  - Default Port: 5432
  - Default User: postgres (or taskflow for this project)
  - Default Password: Set during installation

### 2. Redis (Required - Cache & Queue)

- **Version**: 6.0 or later
- **Download**: https://redis.io/download
- **Purpose**: Caching, circuit breaker state, health checks, recovery history
- **Installation**:

  ```bash
  # macOS (Homebrew)
  brew install redis

  # Ubuntu/Debian
  sudo apt-get install redis-server

  # Windows (via WSL2 or native binary)
  # Download from https://github.com/tporadowski/redis/releases

  # Or use Docker (recommended)
  docker pull redis:7-alpine
  ```

- **Configuration**:
  - Default Port: 6379
  - Default Password: None (optional)
  - Persistence: AOF or RDB recommended for production

### 3. Docker & Docker Compose (Optional but Recommended)

- **Docker**:
  - **Version**: 20.10 or later
  - **Download**: https://www.docker.com/products/docker-desktop
  - **Purpose**: Containerized deployment and local development
- **Docker Compose**:
  - **Version**: 2.0 or later
  - **Included** with Docker Desktop
  - **Purpose**: Multi-container orchestration
- **Installation**:
  ```bash
  docker --version
  docker-compose --version
  ```

### 4. Prometheus (Optional - Metrics Collection)

- **Version**: 2.30 or later
- **Download**: https://prometheus.io/download/
- **Purpose**: Time-series metrics database
- **Installation**:
  ```bash
  # Included in docker-compose.yml
  docker pull prom/prometheus:latest
  ```

### 5. Grafana (Optional - Visualization)

- **Version**: 8.0 or later
- **Download**: https://grafana.com/grafana/download
- **Purpose**: Metrics visualization and dashboards
- **Installation**:
  ```bash
  # Included in docker-compose.yml
  docker pull grafana/grafana:latest
  ```

### 6. Jaeger (Optional - Distributed Tracing)

- **Version**: 1.20 or later
- **Download**: https://www.jaegertracing.io/download/
- **Purpose**: Distributed tracing and request flow visualization
- **Installation**:
  ```bash
  docker pull jaegertracing/all-in-one:latest
  ```

### 7. Git (Required - Version Control)

- **Version**: 2.20 or later
- **Download**: https://git-scm.com/downloads
- **Purpose**: Source code management
- **Verify**:
  ```bash
  git --version
  ```

### 8. Make (Recommended - Build Tool)

- **Version**: GNU Make 4.0+
- **Installation**:

  ```bash
  # macOS
  brew install make

  # Ubuntu/Debian
  sudo apt-get install build-essential

  # Windows (via Chocolatey)
  choco install make
  ```

- **Purpose**: Simplified command running via Makefile

---

## Python Dependencies

### Core Dependencies (requirements.txt)

| Package                       | Version | Purpose                 |
| ----------------------------- | ------- | ----------------------- |
| fastapi                       | 0.104.1 | Web framework           |
| uvicorn                       | 0.24.0  | ASGI server             |
| sqlalchemy                    | 2.0.23  | ORM database            |
| psycopg2-binary               | 2.9.9   | PostgreSQL driver       |
| redis                         | 5.0.1   | Redis client            |
| prometheus-client             | 0.19.0  | Metrics export          |
| opentelemetry-api             | 1.21.0  | Tracing API             |
| opentelemetry-sdk             | 1.21.0  | Tracing SDK             |
| opentelemetry-exporter-otlp   | 1.21.0  | OTLP exporter           |
| opentelemetry-instrumentation | 0.42b0  | Auto-instrumentation    |
| structlog                     | 23.3.0  | Structured logging      |
| pydantic                      | 2.5.0   | Data validation         |
| croniter                      | 2.0.1   | Cron expression parsing |
| python-dotenv                 | 1.0.0   | Environment variables   |
| httpx                         | 0.25.0  | HTTP client             |
| psutil                        | 5.9.6   | System metrics          |
| alembic                       | 1.13.0  | Database migrations     |

### Development Dependencies (requirements-dev.txt)

| Package         | Version | Purpose                |
| --------------- | ------- | ---------------------- |
| pytest          | 7.4.3   | Testing framework      |
| pytest-cov      | 4.1.0   | Coverage reporting     |
| pytest-asyncio  | 0.21.1  | Async test support     |
| black           | 23.12.0 | Code formatting        |
| ruff            | 0.1.8   | Linting                |
| mypy            | 1.7.1   | Type checking          |
| isort           | 5.13.2  | Import sorting         |
| pre-commit      | 3.5.0   | Git hooks              |
| memory-profiler | 0.61.0  | Memory profiling       |
| hypothesis      | 6.92.1  | Property-based testing |

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## Database Setup

### PostgreSQL Setup

#### 1. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE taskqueue;

# Create user (if not exists)
CREATE USER taskflow WITH PASSWORD 'password';

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE taskqueue TO taskflow;

# Exit
\q
```

#### 2. Connection String Format

```
postgresql://username:password@localhost:5432/taskqueue
```

#### 3. Environment Variable

```bash
# In .env file
DATABASE_URL=postgresql://taskflow:password@localhost:5432/taskqueue
```

#### 4. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Or via Python
python -m src.db.init_db
```

### Redis Setup

#### 1. Start Redis

```bash
# macOS/Linux
redis-server

# Or as service
brew services start redis

# Windows (via WSL2)
wsl redis-server
```

#### 2. Verify Connection

```bash
redis-cli ping
# Should return: PONG
```

#### 3. Environment Variable

```bash
# In .env file
REDIS_URL=redis://localhost:6379/0
```

---

## Installation Steps

### Quick Start (Using Docker - Recommended)

```bash
# 1. Clone repository
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd distributed-task-queue-system

# 2. Start all services
docker-compose up -d

# 3. Initialize database
docker exec taskflow_api python -m src.db.init_db

# 4. Verify
curl http://localhost:8000/health
```

### Manual Installation (Linux/macOS)

```bash
# 1. Clone repository
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd distributed-task-queue-system

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql # Linux

# 5. Start Redis
brew services start redis       # macOS
sudo systemctl start redis-server # Linux

# 6. Create database
createdb taskqueue
psql taskqueue -c "CREATE USER taskflow WITH PASSWORD 'password';"

# 7. Initialize database
alembic upgrade head

# 8. Start API server
python run.py

# 9. In another terminal, start worker
python -m src.worker.main

# 10. Access API at http://localhost:8000
```

### Windows Installation (Native)

```powershell
# 1. Install PostgreSQL
# Download from https://www.postgresql.org/download/windows/

# 2. Install Redis
# Download from https://github.com/tporadowski/redis/releases

# 3. Clone repository
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd "distributed-task-queue-system"

# 4. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 6. Set environment variables
# Create .env file with:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/taskqueue
# REDIS_URL=redis://localhost:6379/0

# 7. Initialize database
alembic upgrade head

# 8. Start services
python run.py
```

---

## Configuration Files

### .env File (Create in project root)

```env
# Database
DATABASE_URL=postgresql://taskflow:password@localhost:5432/taskqueue
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_SSL=false

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Worker
WORKER_CONCURRENCY=5
WORKER_QUEUE_NAME=default
WORKER_HOSTNAME=worker-1

# Monitoring
PROMETHEUS_ENABLED=true
TRACING_ENABLED=true
TRACING_ENDPOINT=http://localhost:4318
TRACING_SAMPLE_RATE=0.1

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Features
ENABLE_SCHEDULING=true
ENABLE_RETRY=true
ENABLE_DLQ=true
MAX_RETRIES=3
RETRY_DELAY_SECONDS=5
```

### requirements.txt (Python)

```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-otlp==1.21.0
structlog==23.3.0
pydantic==2.5.0
croniter==2.0.1
python-dotenv==1.0.0
httpx==0.25.0
psutil==5.9.6
alembic==1.13.0
```

### requirements-dev.txt (Development Only)

```
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
black==23.12.0
ruff==0.1.8
mypy==1.7.1
isort==5.13.2
pre-commit==3.5.0
memory-profiler==0.61.0
```

---

## Verification Checklist

After installation, verify everything works:

```bash
# 1. Check Python
python --version  # Should be 3.9+

# 2. Check PostgreSQL
psql --version

# 3. Check Redis
redis-cli --version

# 4. Check Docker (if using)
docker --version
docker-compose --version

# 5. Check virtual environment
pip list  # Should show FastAPI, SQLAlchemy, etc.

# 6. Test database connection
psql -U taskflow -d taskqueue -c "SELECT 1;"

# 7. Test Redis connection
redis-cli ping

# 8. Test API
curl http://localhost:8000/health

# 9. Run tests
pytest --co  # Collect tests
pytest -v    # Run tests

# 10. Check code quality
black --check src/
ruff check src/
mypy src/
```

---

## Troubleshooting

### Python Version Issues

```bash
# Problem: "python not found"
# Solution: Use python3 instead of python

python3 --version  # Check version
python3 -m venv venv  # Create venv
```

### PostgreSQL Connection Issues

```bash
# Problem: "could not connect to server"
# Solution: Verify PostgreSQL is running

# macOS
brew services list | grep postgres

# Linux
sudo systemctl status postgresql

# Windows
# Check Services or use Windows Task Manager
```

### Redis Connection Issues

```bash
# Problem: "Connection refused"
# Solution: Verify Redis is running

redis-cli ping  # Should return PONG
```

### Docker Issues

```bash
# Problem: "port already in use"
# Solution: Kill existing container

docker-compose down
docker ps -a  # Check running containers
docker rm container_name
```

### Permission Errors

```bash
# Problem: "Permission denied"
# Solution: Use sudo for system-level operations

sudo systemctl start postgresql
sudo systemctl start redis-server
```

---

## Environment Variables Summary

| Variable           | Required | Default | Description                  |
| ------------------ | -------- | ------- | ---------------------------- |
| DATABASE_URL       | Yes      | -       | PostgreSQL connection string |
| REDIS_URL          | Yes      | -       | Redis connection string      |
| API_HOST           | No       | 0.0.0.0 | API bind address             |
| API_PORT           | No       | 8000    | API port                     |
| DEBUG              | No       | false   | Debug mode                   |
| LOG_LEVEL          | No       | INFO    | Logging level                |
| WORKER_CONCURRENCY | No       | 5       | Tasks per worker             |
| PROMETHEUS_ENABLED | No       | true    | Enable metrics               |
| TRACING_ENABLED    | No       | true    | Enable tracing               |

---

## Support & Resources

### Documentation

- **API Reference**: See [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **Deployment**: See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### External Links

- **Python**: https://www.python.org/
- **PostgreSQL**: https://www.postgresql.org/
- **Redis**: https://redis.io/
- **Docker**: https://www.docker.com/
- **FastAPI**: https://fastapi.tiangolo.com/

### Getting Help

- Check [docs/TROUBLESHOOTING_AND_BEST_PRACTICES.md](docs/TROUBLESHOOTING_AND_BEST_PRACTICES.md)
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Open an issue on GitHub

---

## Summary Checklist

Before starting development:

- [ ] Python 3.9+ installed
- [ ] PostgreSQL 12+ installed and running
- [ ] Redis 6.0+ installed and running
- [ ] Git installed
- [ ] Virtual environment created
- [ ] Python dependencies installed
- [ ] Database initialized
- [ ] .env file configured
- [ ] `pytest` runs successfully
- [ ] API starts with `python run.py`
- [ ] Worker starts with `python -m src.worker.main`

**Status**: ✅ All requirements documented and ready for setup!
