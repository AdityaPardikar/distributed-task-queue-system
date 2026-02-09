# Week 5 Quick Start Guide

**🚀 For New Context Window - Read This First!**

---

## ⚡ 30-Second Project Status

- **Project**: Production-grade distributed task queue with email campaign system
- **Week**: Starting Week 5 (Days 1-7)
- **Backend**: ✅ 100% unit tests passing (79/79)
- **Frontend**: ✅ 99.5% tests passing (198/199)
- **Status**: Production-ready backend, needs Week 5 enhancements

---

## 🎯 Week 5 Top Priorities (In Order)

1. **Authentication System (Day 1)** - JWT, RBAC, API keys
2. **Fix Integration Tests (Day 7)** - Currently 0% passing, blocks prod
3. **Monitoring Infrastructure (Day 2)** - OpenTelemetry, Grafana dashboards
4. **Increase Test Coverage (Day 7)** - From 40% to 80%+
5. **Security Audit (Day 7)** - No HIGH/CRITICAL vulnerabilities

---

## 📂 Project Structure (Essential Files)

```
DISTRIBUTED TASK QUEUE SYSTEM/
├── src/api/main.py              # FastAPI app (13 routers loaded)
├── src/models/__init__.py       # 11 database models (Task, Worker, Campaign...)
├── src/core/broker.py           # Redis task queue
├── tests/conftest.py            # ⭐ CRITICAL: Test fixtures with StaticPool
├── tests/unit/                  # 79 tests, all passing
├── tests/integration/           # ❌ Needs fixing Week 5
├── frontend/src/                # React dashboard
└── docker-compose.yml           # Multi-container setup
```

---

## 🔧 Critical Fixes from Week 4 (Context for Week 5)

### Fixed Issues (Don't Re-Fix!)

1. ✅ **SQLAlchemy Task relationships** - Parent/children now working
2. ✅ **Test database pooling** - Using `StaticPool` for SQLite in-memory
3. ✅ **TrustedHostMiddleware** - Skipped in test env (`APP_ENV=test`)
4. ✅ **Campaign model** - `created_by` now Optional
5. ✅ **Templates router** - Fixed double prefix
6. ✅ **Test fixtures** - Consolidated in `conftest.py`
7. ✅ **Model imports** - All 11 models imported in conftest

### Known Issues (Week 5 Must Fix)

1. ❌ **Integration tests failing** - 0% pass rate
2. ❌ **No authentication** - Security vulnerability
3. ❌ **Code coverage 40%** - Need 80%+
4. ❌ **61 Pydantic warnings** - Deprecations to fix
5. ❌ **No monitoring** - Need observability stack

---

## 🚀 Quick Start Commands

### Verify Setup

```bash
cd "C:\PROJECT\DISTRIBUTED TASK QUEUE SYSTEM"

# Check backend tests (should be 79/79 passing)
python -m pytest tests/unit/ -q

# Check frontend tests (should be 198/199 passing)
cd frontend && npm test && cd ..
```

### Run Development Environment

```bash
# Backend API
uvicorn src.api.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm run dev

# Or use Docker
docker-compose up -d
```

### Useful Test Commands

```bash
# Run specific test file
python -m pytest tests/unit/test_task_api.py -v

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=html

# Run integration tests (currently failing)
python -m pytest tests/integration/ -v
```

---

## 🔑 Key Facts to Remember

### Database Models (11 tables)

- **Task** - Main task entity with parent/children relationships
- **Worker** - Worker pool management
- **Campaign** - Email campaign orchestration
- **TaskResult** - Task execution results
- **TaskExecution** - Execution history
- **EmailRecipient** - Campaign recipient tracking
- **EmailTemplate** - Reusable email templates
- **TaskLog** - Task execution logs
- **CampaignTask** - Campaign-task linkage
- **DeadLetterQueue** - Failed task management
- **Alert** - System alerts

### API Routers (13 loaded in main.py)

- tasks, workers, campaigns, templates, analytics
- dashboard, search, workflows, alerts, metrics
- resilience, debug, auth (placeholder)

### Technology Stack

- **Backend**: FastAPI + SQLAlchemy + Redis + PostgreSQL/SQLite
- **Frontend**: React + TypeScript + Tailwind + Recharts
- **Infrastructure**: Docker + Nginx + Prometheus

---

## ⚠️ Critical Gotchas (Lessons from Week 4)

### Test Configuration

```python
# MUST set before importing app in test files
import os
os.environ["APP_ENV"] = "test"
```

### Database Fixtures

```python
# tests/conftest.py uses StaticPool - DON'T change
from sqlalchemy.pool import StaticPool
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Required for test DB!
)
```

### Router Prefixes

```python
# In router files (tasks.py, workers.py, etc.)
router = APIRouter(prefix="/tasks", tags=["tasks"])

# In main.py
app.include_router(tasks.router, prefix="/api/v1")

# Result: /api/v1/tasks
```

### Model Imports

```python
# tests/conftest.py MUST import all models
from src.models import (
    Base, Task, Worker, Campaign, TaskResult, TaskLog,
    TaskExecution, EmailRecipient, EmailTemplate,
    CampaignTask, DeadLetterQueue, Alert,
)
# Otherwise tables won't be created!
```

---

## 📋 Week 5 Daily Focus

| Day | Focus                          | Priority | Deliverables                          |
| --- | ------------------------------ | -------- | ------------------------------------- |
| 1   | **Authentication & RBAC**      | 🔴 P0    | JWT system, login UI, 20+ tests       |
| 2   | **Monitoring & Observability** | 🔴 P0    | OpenTelemetry, Grafana, 5+ dashboards |
| 3   | **Resilience Patterns**        | 🟡 P1    | Circuit breakers, retry policies      |
| 4   | **Workflow Engine**            | 🟡 P1    | DAG support, conditional execution    |
| 5   | **Performance Optimization**   | 🟡 P1    | DB tuning, load testing               |
| 6   | **Backup & Operations**        | 🟡 P1    | Backup scripts, runbooks              |
| 7   | **Final QA & Production**      | 🔴 P0    | 100% tests, 80% coverage, security    |

---

## 🎯 Week 5 Success Criteria (Checklist)

### Must Have (P0)

- [ ] Authentication system with JWT
- [ ] Integration tests 100% passing
- [ ] Code coverage ≥ 80%
- [ ] All Pydantic warnings fixed
- [ ] Security audit passed (no HIGH/CRITICAL vulns)
- [ ] Load test passing (1000+ RPS)

### Should Have (P1)

- [ ] Circuit breaker implementation
- [ ] Advanced workflow engine
- [ ] Database optimization completed
- [ ] Backup/restore procedures tested
- [ ] Operational runbooks written

---

## 📊 Current Metrics (Week 4 End State)

| Metric             | Current            | Target Week 5  |
| ------------------ | ------------------ | -------------- |
| Backend Unit Tests | 79/79 (100%) ✅    | 100/100 (100%) |
| Integration Tests  | 0/? (0%) ❌        | ?/? (100%)     |
| Frontend Tests     | 198/199 (99.5%) ✅ | 199/199 (100%) |
| Code Coverage      | ~40% ❌            | 80%+           |
| API Latency (p95)  | Not measured       | <200ms         |
| Task Throughput    | Not measured       | 1000+/sec      |

---

## 🔍 Debugging Tips

### Tests Failing After Changes?

1. Check `os.environ["APP_ENV"] = "test"` set before imports
2. Verify fixtures in `tests/conftest.py` not modified
3. Run single test: `pytest tests/unit/test_file.py::test_name -v`
4. Check test database has tables: `Base.metadata.tables.keys()`

### Import Errors?

1. Check in project root: `cd "C:\PROJECT\DISTRIBUTED TASK QUEUE SYSTEM"`
2. Virtual environment activated?
3. Dependencies installed: `pip install -r requirements.txt`

### API Errors in Tests?

1. Check TrustedHostMiddleware skipped: `settings.APP_ENV != "test"`
2. Verify router loaded in `main.py`
3. Check endpoint prefix: `/api/v1/{router_prefix}`

---

## 📚 Essential Documentation

- **Full Roadmap**: `docs/WEEK5_ROADMAP.md` (this file's parent)
- **Week 4 Summary**: `docs/WEEK4_COMPLETION.md`
- **API Reference**: `docs/API.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Deployment**: `docs/DEPLOYMENT.md`

---

## 🎬 Start Week 5 Now!

```bash
# 1. Verify current state
python -m pytest tests/unit/ -v  # Should be 79/79 ✅

# 2. Read full roadmap
cat docs/WEEK5_ROADMAP.md

# 3. Start Day 1 (Authentication)
# Create feature branch
git checkout -b week5-day1-authentication

# 4. Begin implementing JWT auth system
# (Follow Day 1 tasks in WEEK5_ROADMAP.md)
```

---

**Ready to build production-grade features! 🚀**

_Quick Start Guide - February 9, 2026_
