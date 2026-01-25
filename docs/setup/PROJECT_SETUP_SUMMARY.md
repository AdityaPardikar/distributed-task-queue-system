# Project Setup & Requirements Summary

## ✅ Status: Week 1 & 2 Complete

All features from Week 1 and Week 2 are **fully implemented, tested, documented, and pushed to GitHub**.

---

## Project Overview

**Distributed Task Queue System** - Production-ready task management platform with:

- 45+ API endpoints
- 100+ test cases (80%+ coverage)
- Comprehensive monitoring & observability
- Production resilience patterns
- Complete deployment documentation

**Repository**: https://github.com/AdityaPardikar/distributed-task-queue-system

---

## Complete Requirements Checklist

### Operating System

- ✅ **Linux**: Ubuntu 18.04+, Debian 9+, CentOS 7+
- ✅ **macOS**: 10.14+ (Intel or Apple Silicon)
- ✅ **Windows**: 10/11 with WSL2 (recommended) or native

### Hardware

- **Minimum**: 2 CPU cores, 4GB RAM, 20GB disk space
- **Recommended**: 4 CPU cores, 8GB RAM, 100GB disk space

---

## External Applications to Download & Install

### 1. **Python 3.9+** (REQUIRED)

- **Download**: https://www.python.org/downloads/
- **Verify**: `python3 --version`
- **Purpose**: Runtime for FastAPI backend

### 2. **PostgreSQL 12+** (REQUIRED)

- **Download**: https://www.postgresql.org/download/
- **Purpose**: Primary relational database
- **Install**:
  - **macOS**: `brew install postgresql@15`
  - **Ubuntu**: `sudo apt-get install postgresql postgresql-contrib`
  - **Windows**: Download installer or use Docker
- **Verify**: `psql --version`

### 3. **Redis 6.0+** (REQUIRED)

- **Download**: https://redis.io/download
- **Purpose**: Cache, queue state, circuit breaker storage
- **Install**:
  - **macOS**: `brew install redis`
  - **Ubuntu**: `sudo apt-get install redis-server`
  - **Windows**: WSL2 or https://github.com/tporadowski/redis/releases
- **Verify**: `redis-cli --version`

### 4. **Git 2.20+** (REQUIRED)

- **Download**: https://git-scm.com/downloads
- **Purpose**: Version control & repository cloning
- **Verify**: `git --version`

### 5. **Docker & Docker Compose** (OPTIONAL - Recommended)

- **Download**: https://www.docker.com/products/docker-desktop
- **Purpose**: Containerized local development and production deployment
- **Version**: Docker 20.10+, Docker Compose 2.0+
- **Verify**:
  ```bash
  docker --version
  docker-compose --version
  ```

### 6. **Make** (OPTIONAL - Convenience)

- **Install**:
  - **macOS**: `brew install make`
  - **Ubuntu**: `sudo apt-get install build-essential`
  - **Windows**: `choco install make`
- **Purpose**: Simplified command execution via Makefile

### 7. **Prometheus** (OPTIONAL - Metrics)

- **Included in Docker**: `docker pull prom/prometheus:latest`
- **Purpose**: Time-series metrics collection
- **Access**: http://localhost:9090 (when running)

### 8. **Grafana** (OPTIONAL - Visualization)

- **Included in Docker**: `docker pull grafana/grafana:latest`
- **Purpose**: Metrics dashboard visualization
- **Access**: http://localhost:3001 (when running, user: admin, pass: admin)

### 9. **Jaeger** (OPTIONAL - Distributed Tracing)

- **Included in Docker**: `docker pull jaegertracing/all-in-one:latest`
- **Purpose**: Request tracing and visualization
- **Access**: http://localhost:16686 (when running)

---

## Python Dependencies (Auto-Installed)

### Core Packages (requirements.txt)

```
fastapi==0.104.1           # Web framework
uvicorn==0.24.0            # ASGI server
sqlalchemy==2.0.23         # ORM
psycopg2-binary==2.9.9     # PostgreSQL driver
redis==5.0.1               # Redis client
prometheus-client==0.19.0  # Metrics
opentelemetry-api==1.21.0  # Tracing
structlog==23.3.0          # Logging
pydantic==2.5.0            # Validation
croniter==2.0.1            # Scheduling
python-dotenv==1.0.0       # Config
```

### Development Packages (requirements-dev.txt)

```
pytest==7.4.3              # Testing
black==23.12.0             # Formatting
ruff==0.1.8                # Linting
mypy==1.7.1                # Type checking
```

---

## Quick Start Guide

### Option 1: Docker (Recommended - 5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd distributed-task-queue-system

# 2. Start development stack (PostgreSQL + Redis)
docker-compose -f deployment/docker/docker-compose.dev.yml up -d

# 3. Verify services are running
docker-compose -f deployment/docker/docker-compose.dev.yml ps

# 4. Test database
docker-compose -f deployment/docker/docker-compose.dev.yml exec postgres psql -U taskflow -d taskqueue -c "SELECT 1;"

# 5. Test Redis
docker-compose -f deployment/docker/docker-compose.dev.yml exec redis redis-cli ping

# 6. Install Python dependencies
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 7. Initialize database
alembic upgrade head

# 8. Start API server
python run.py

# 9. In new terminal, start worker
python -m src.worker.main

# 10. Access API at http://localhost:8000
# 11. API docs at http://localhost:8000/docs
```

### Option 2: Manual Setup (Linux/macOS - 15 minutes)

```bash
# 1. Clone repository
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd distributed-task-queue-system

# 2. Start PostgreSQL (if not already running)
brew services start postgresql  # macOS
sudo systemctl start postgresql # Linux

# 3. Start Redis (if not already running)
brew services start redis       # macOS
sudo systemctl start redis-server # Linux

# 4. Create database
createdb taskqueue
psql taskqueue -c "CREATE USER taskflow WITH PASSWORD 'password';"

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 7. Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://taskflow:password@localhost:5432/taskqueue
REDIS_URL=redis://localhost:6379/0
API_PORT=8000
DEBUG=true
EOF

# 8. Initialize database
alembic upgrade head

# 9. Start API server
python run.py

# 10. In new terminal, start worker
python -m src.worker.main

# 11. Access API at http://localhost:8000
```

### Option 3: Windows Native Setup

```powershell
# 1. Install prerequisites using Chocolatey (or download manually)
choco install python postgresql redis git docker-desktop

# 2. Clone repository
git clone https://github.com/AdityaPardikar/distributed-task-queue-system.git
cd "distributed-task-queue-system"

# 3. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Create .env file
@"
DATABASE_URL=postgresql://postgres:password@localhost:5432/taskqueue
REDIS_URL=redis://localhost:6379/0
API_PORT=8000
DEBUG=true
"@ | Out-File -Encoding UTF8 .env

# 6. Initialize database
alembic upgrade head

# 7. Start API server
python run.py

# 8. Start worker in new PowerShell window
python -m src.worker.main
```

---

## File Organization

### Main Project Structure

```
project/
├── src/                          # Source code
│   ├── api/                      # FastAPI routes & models
│   ├── core/                     # Business logic
│   ├── db/                       # Database & migrations
│   ├── worker/                   # Worker service
│   ├── resilience/               # Error handling patterns
│   └── monitoring/               # Observability
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── deployment/                   # Deployment configs
│   ├── docker/                   # Docker files
│   │   ├── Dockerfile.api        # API container
│   │   ├── Dockerfile.worker     # Worker container
│   │   ├── docker-compose.dev.yml  # Local development
│   │   └── docker-compose.prod.yml # Production
│   └── k8s/                      # Kubernetes manifests
├── docs/                         # Documentation
│   ├── API_REFERENCE.md          # API endpoints (500+ lines)
│   ├── DEPLOYMENT_GUIDE.md       # Deployment (400+ lines)
│   ├── MONITORING_GUIDE.md       # Monitoring (400+ lines)
│   └── TROUBLESHOOTING_AND_BEST_PRACTICES.md (600+ lines)
├── monitoring/                   # Prometheus, logging configs
├── scripts/                      # Utility scripts
├── REQUIREMENTS_AND_SETUP.md     # This file
├── DOCKER_USAGE.md               # Docker reference
├── CONTRIBUTING.md               # Development guidelines
├── docker-compose.yml            # Main compose reference
├── docker-compose.local.yml      # Dev compose reference
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Dev dependencies
├── .env.example                  # Example config
├── Makefile                      # Convenience commands
└── run.py                        # API entry point
```

---

## Key Documentation Files

| File                                  | Purpose                       | Lines |
| ------------------------------------- | ----------------------------- | ----- |
| REQUIREMENTS_AND_SETUP.md             | Complete installation guide   | 400+  |
| DOCKER_USAGE.md                       | Docker commands & workflow    | 300+  |
| API_REFERENCE.md                      | API endpoint documentation    | 500+  |
| DEPLOYMENT_GUIDE.md                   | Production deployment         | 400+  |
| MONITORING_GUIDE.md                   | Observability setup           | 400+  |
| TROUBLESHOOTING_AND_BEST_PRACTICES.md | Common issues & solutions     | 600+  |
| CONTRIBUTING.md                       | Development guidelines        | 400+  |
| WEEK_2_COMPLETION_SUMMARY.md          | Summary of all work completed | 400+  |

---

## Docker Commands Quick Reference

### Development (PostgreSQL + Redis only)

```bash
# Start
docker-compose -f deployment/docker/docker-compose.dev.yml up -d

# Stop
docker-compose -f deployment/docker/docker-compose.dev.yml down

# View logs
docker-compose -f deployment/docker/docker-compose.dev.yml logs -f
```

### Production (Full stack with monitoring)

```bash
# Start
docker-compose -f deployment/docker/docker-compose.prod.yml up -d

# View services
docker-compose -f deployment/docker/docker-compose.prod.yml ps

# Access services
# API: http://localhost:8000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

---

## Verification Checklist

After installation, verify everything works:

```bash
# ✅ Python
python3 --version  # Should be 3.9+

# ✅ PostgreSQL
psql --version

# ✅ Redis
redis-cli --version

# ✅ Git
git --version

# ✅ Docker (if using)
docker --version

# ✅ Database connection
psql -U taskflow -d taskqueue -c "SELECT 1;"

# ✅ Redis connection
redis-cli ping  # Should return PONG

# ✅ Python packages
pip list | grep fastapi

# ✅ Run tests
pytest --co  # Collect tests
pytest -v    # Run tests

# ✅ Start API
python run.py  # Should start on http://localhost:8000

# ✅ Health check
curl http://localhost:8000/health
```

---

## Environment Variables

### Required

```env
DATABASE_URL=postgresql://taskflow:password@localhost:5432/taskqueue
REDIS_URL=redis://localhost:6379/0
```

### Optional (Defaults provided)

```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
LOG_LEVEL=INFO
WORKER_CONCURRENCY=5
PROMETHEUS_ENABLED=true
TRACING_ENABLED=true
```

See `.env.example` for complete reference.

---

## Troubleshooting

### "Python not found"

- Use `python3` instead of `python`
- Add Python to PATH on Windows

### "PostgreSQL connection refused"

- Verify: `brew services list | grep postgres` (macOS)
- Or: `sudo systemctl status postgresql` (Linux)
- Start: `brew services start postgresql` or `sudo systemctl start postgresql`

### "Redis connection refused"

- Verify: `redis-cli ping`
- Start: `brew services start redis` or `sudo systemctl start redis-server`

### "Port 5432 already in use"

- Find process: `lsof -i :5432`
- Kill: `kill -9 <PID>`

### Docker permission errors

- Add user to docker group: `sudo usermod -aG docker $USER`
- Or use `sudo docker` commands

---

## Support & Resources

### Documentation

- **Setup**: REQUIREMENTS_AND_SETUP.md (this file)
- **Docker**: DOCKER_USAGE.md
- **API**: docs/API_REFERENCE.md
- **Deployment**: docs/DEPLOYMENT_GUIDE.md
- **Monitoring**: docs/MONITORING_GUIDE.md
- **Troubleshooting**: docs/TROUBLESHOOTING_AND_BEST_PRACTICES.md

### External Links

- Python: https://www.python.org/
- PostgreSQL: https://www.postgresql.org/
- Redis: https://redis.io/
- Docker: https://www.docker.com/
- FastAPI: https://fastapi.tiangolo.com/

### Community

- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions
- CONTRIBUTING.md: Development guidelines

---

## Summary

✅ **All requirements documented**
✅ **Multiple installation options provided** (Docker, manual, Windows)
✅ **Quick start guide available**
✅ **Comprehensive documentation**
✅ **Production-ready system**

### What You Need to Download

1. **Python 3.9+**
2. **PostgreSQL 12+**
3. **Redis 6.0+**
4. **Git**
5. **Docker** (optional but recommended)

That's it! Everything else installs automatically via pip.

---

**Status**: ✅ Week 1 & 2 Complete - Production Ready
