# Project Context - For New Conversation Window

**Copy this entire document and paste it at the start of a new conversation to load project context quickly.**

---

## Project Overview

I'm working on a **production-grade Distributed Task Queue System** with an email campaign management feature. This is Week 5 of development.

### Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Redis, PostgreSQL/SQLite
- **Frontend**: React 18, TypeScript, Tailwind CSS, Recharts
- **Testing**: Pytest (backend), Jest (frontend)
- **Infrastructure**: Docker, Docker Compose, Nginx

### Project Location

```
C:\PROJECT\DISTRIBUTED TASK QUEUE SYSTEM\
```

---

## Current Status (End of Week 4)

### ✅ What's Working Perfectly

**Backend**:

- 79/79 unit tests passing (100%) ✅
- Full REST API with 13 routers (tasks, workers, campaigns, templates, analytics, etc.)
- 11 database models (Task, Worker, Campaign, EmailTemplate, etc.)
- Redis-based task queue with priority support
- Email campaign system with Jinja2 templates
- Worker pool management with heartbeat monitoring
- SQLAlchemy models with proper relationships

**Frontend**:

- 198/199 tests passing (99.5%) ✅
- React dashboard with real-time metrics
- Task management UI
- Campaign management UI
- Advanced filtering and search
- Analytics dashboard with Recharts
- Worker monitoring interface

**Infrastructure**:

- Docker containerization complete
- Docker Compose multi-container setup
- Development and production configs

### ❌ Known Issues (Week 5 Must Fix)

1. **Integration tests failing** - 0% pass rate (infrastructure setup issues)
2. **No authentication** - Security vulnerability, need JWT + RBAC
3. **Low code coverage** - 40% (need 80%+)
4. **Pydantic v2 warnings** - 61 deprecation warnings to fix
5. **No monitoring** - Need OpenTelemetry + Grafana

---

## Critical Code Patterns (From Week 4 Fixes)

### Test Configuration (MUST USE)

```python
# In ALL test files, before imports:
import os
os.environ["APP_ENV"] = "test"
```

### Database Test Fixture (tests/conftest.py)

```python
from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # REQUIRED - don't change!
    )
    Base.metadata.create_all(engine)
    return engine
```

### Model Imports (tests/conftest.py)

```python
# ALL models MUST be imported for tables to be created
from src.models import (
    Base, Task, Worker, Campaign, TaskResult, TaskLog,
    TaskExecution, EmailRecipient, EmailTemplate,
    CampaignTask, DeadLetterQueue, Alert,
)
```

### Router Pattern

```python
# In route files (e.g., tasks.py):
router = APIRouter(prefix="/tasks", tags=["tasks"])

# In main.py:
app.include_router(tasks.router, prefix="/api/v1")
# Results in: /api/v1/tasks
```

### TrustedHostMiddleware (main.py)

```python
# Skip in test environment
if settings.APP_ENV != "test":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)
```

---

## Week 5 Plan (7 Days)

**Day 1**: Authentication & Authorization (JWT, RBAC, API keys)  
**Day 2**: Advanced Monitoring (OpenTelemetry, Grafana, structured logging)  
**Day 3**: Resilience Patterns (circuit breakers, retry policies, chaos engineering)  
**Day 4**: Advanced Workflow Engine (task dependencies, conditional execution, DAG)  
**Day 5**: Performance Optimization (DB tuning, load testing, memory profiling)  
**Day 6**: Backup & Operations (backup scripts, runbooks, HA documentation)  
**Day 7**: Final QA & Production Readiness (fix integration tests, 80% coverage, security audit)

### Top Priorities (P0)

1. Implement JWT authentication system (Day 1)
2. Fix ALL integration tests to 100% passing (Day 7)
3. Increase code coverage from 40% to 80%+ (Day 7)
4. Fix 61 Pydantic deprecation warnings (Day 7)
5. Pass security audit - no HIGH/CRITICAL vulnerabilities (Day 7)

---

## Key Files Reference

### Backend Core

- `src/api/main.py` - FastAPI app factory, 13 routers loaded
- `src/models/__init__.py` - All 11 database models
- `src/core/broker.py` - Redis task queue implementation
- `src/core/worker.py` - Task execution worker
- `src/core/scheduler.py` - Cron scheduler
- `src/api/routes/` - 13 API routers

### Testing

- `tests/conftest.py` - ⭐ CRITICAL: Shared fixtures (StaticPool, model imports)
- `tests/unit/` - 79 tests, all passing
- `tests/integration/` - Needs fixing Week 5

### Configuration

- `src/config/settings.py` - Environment-based configuration
- `docker-compose.yml` - Multi-container orchestration
- `.env.example` - Environment variables template

### Documentation

- `docs/WEEK5_ROADMAP.md` - Detailed Week 5 plan
- `docs/WEEK5_QUICK_START.md` - Quick reference guide
- `docs/WEEK4_COMPLETION.md` - Week 4 summary
- `docs/API.md` - API reference

---

## Common Commands

### Run Tests

```bash
# Backend unit tests (should be 79/79 passing)
python -m pytest tests/unit/ -v

# Integration tests (currently failing)
python -m pytest tests/integration/ -v

# Frontend tests (should be 198/199 passing)
cd frontend && npm test && cd ..

# With coverage
python -m pytest tests/unit/ --cov=src --cov-report=html
```

### Development

```bash
# Backend API (port 8000)
uvicorn src.api.main:app --reload

# Frontend (port 3000)
cd frontend && npm run dev

# Docker
docker-compose up -d
docker-compose logs -f backend
```

### Code Quality

```bash
# Format Python code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
pylint src/
```

---

## Recent Major Fixes (Week 4 Lessons)

1. **SQLAlchemy Task Model** - Fixed parent/children relationship with `remote_side=[task_id]`
2. **Test Database** - Must use `StaticPool` for SQLite in-memory persistence
3. **Campaign Model** - Made `created_by` Optional to allow None in tests
4. **Templates Router** - Fixed double prefix issue (`/api/v1/templates` not `/api/v1/api/v1/templates`)
5. **Serializer** - Added base64 encoding for binary data in JSON
6. **Test Fixtures** - Consolidated all fixtures in `tests/conftest.py`

---

## Week 5 Success Criteria

- [ ] Authentication system with JWT + RBAC operational
- [ ] 100% integration tests passing
- [ ] 80%+ code coverage
- [ ] Zero Pydantic deprecation warnings
- [ ] Security audit passed (no HIGH/CRITICAL vulnerabilities)
- [ ] Load test passing at 1000+ requests/second
- [ ] Monitoring infrastructure deployed (Grafana dashboards)
- [ ] Operational runbooks documented

---

## Request Format for AI Assistant

When asking for help, please:

1. **Specify the task clearly**: "Implement JWT authentication in FastAPI"
2. **Mention relevant files**: "Update src/api/main.py and create src/auth/"
3. **Reference existing patterns**: "Follow the router pattern used in tasks.py"
4. **State testing requirements**: "Add tests in tests/unit/test_auth.py with 100% coverage"
5. **Run tests after changes**: "Verify with: pytest tests/unit/test_auth.py -v"

### Example Good Request

"I need to implement JWT authentication for Week 5 Day 1. Please:

1. Create src/auth/jwt.py with token generation/validation functions
2. Add User model to src/models/**init**.py with roles (admin, operator, viewer)
3. Create /api/v1/auth/login and /api/v1/auth/register endpoints in src/api/routes/auth.py
4. Add @require_auth decorator for protecting endpoints
5. Write comprehensive tests in tests/unit/test_auth.py
6. Follow the existing router pattern from tasks.py"

---

## Important Conventions

### Git Workflow

```bash
# Create feature branch
git checkout -b week5-day1-auth

# Commit frequently
git add .
git commit -m "feat: Add JWT authentication system"
```

### Code Style

- Use Python type hints everywhere
- Document all public functions/classes
- Write tests BEFORE implementation (TDD)
- Keep functions under 50 lines
- Follow PEP 8

### Testing

- Every new feature needs tests
- Maintain 100% unit test pass rate
- Use pytest fixtures from conftest.py
- Mock external services (Redis, email provider)

---

## Troubleshooting Checklist

**Tests failing?**

1. ✓ Check `os.environ["APP_ENV"] = "test"` is set
2. ✓ Verify conftest.py imports all models
3. ✓ Confirm StaticPool used in test engine
4. ✓ Run single test to isolate issue

**Import errors?**

1. ✓ In project root directory
2. ✓ Virtual environment activated
3. ✓ Dependencies installed: `pip install -r requirements.txt`

**API 404 errors in tests?**

1. ✓ Router has correct prefix (e.g., "/tasks" not "/api/v1/tasks")
2. ✓ Router included in main.py with `app.include_router(router, prefix="/api/v1")`
3. ✓ Middleware not blocking test requests

---

## Ready to Start Week 5!

**First thing to do**: Read the full roadmap at `docs/WEEK5_ROADMAP.md`

**Then**: Begin Day 1 authentication implementation

**Remember**: Test frequently, document as you go, maintain 100% unit test pass rate

**Good luck! 🚀**

---

_Context Document - February 9, 2026_
_For use in new conversation windows_
