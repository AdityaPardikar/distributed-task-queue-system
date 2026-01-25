# Contributing to Distributed Task Queue System

## Welcome Contributors! 👋

We appreciate contributions! This guide helps you get started.

---

## Getting Started

### 1. Fork & Clone
```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/task-queue.git
cd task-queue
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies with dev extras
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### 3. Configure Local Database
```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE taskqueue_dev;"

# Set environment variables
export DATABASE_URL="postgresql://postgres:password@localhost/taskqueue_dev"
export REDIS_URL="redis://localhost:6379"

# Run migrations
alembic upgrade head
```

### 4. Start Services (Docker)
```bash
# Start PostgreSQL and Redis
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Verify
psql $DATABASE_URL -c "SELECT 1;"
redis-cli ping
```

---

## Development Workflow

### Before Starting
1. Check [GitHub Issues](https://github.com/taskqueue/issues) for existing work
2. Create issue if not exists: "I'd like to work on..."
3. Ask maintainers if unclear

### Creating a Feature Branch
```bash
git checkout -b feature/my-feature
# Or: bug/issue-description
```

### Making Changes

#### Code Style
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
ruff check src/ tests/ --fix

# Type checking
mypy src/
```

#### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/integration/test_tasks.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

#### Git Commits
```bash
# Good commit messages follow format:
# <type>: <subject> [<scope>]
#
# <body>
#
# <footer>

# Examples:
# feat: Add circuit breaker pattern
# fix: Handle task timeout edge case
# docs: Update API reference
# test: Add integration tests for resilience
# refactor: Simplify task assignment logic
# perf: Optimize queue depth query
```

### Submitting a Pull Request

1. **Push your branch**:
   ```bash
   git push origin feature/my-feature
   ```

2. **Create PR on GitHub**:
   - Title: Clear and descriptive
   - Description: Reference issue, explain changes
   - Link related issues: "Fixes #123"

3. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type
   - [ ] Bug fix
   - [ ] Feature
   - [ ] Documentation
   - [ ] Performance
   
   ## Checklist
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] Code formatted and linted
   - [ ] Backward compatible
   
   ## Verification
   Steps to test the changes
   ```

4. **Address review feedback**:
   ```bash
   # Make requested changes
   git add .
   git commit --amend
   git push --force-with-lease
   ```

---

## Code Guidelines

### Python Style
- **PEP 8** compliance (use `black`, `ruff`)
- **Type hints** for all functions:
  ```python
  def submit_task(name: str, args: List[Any]) -> Task:
      """Submit a new task."""
      pass
  ```

- **Docstrings** for public APIs:
  ```python
  def submit_task(name: str, args: List[Any]) -> Task:
      """Submit a new task for execution.
      
      Args:
          name: Task name/function to execute
          args: Positional arguments for task
          
      Returns:
          Task object with unique id and status
          
      Raises:
          ValueError: If task name invalid
          DatabaseError: If task persistence fails
      """
      pass
  ```

- **Logging** with structlog:
  ```python
  import structlog
  logger = structlog.get_logger()
  
  logger.info("task_submitted", task_id=task.id, priority=task.priority)
  logger.error("execution_failed", task_id=task.id, error=str(e), exc_info=True)
  ```

### Error Handling
```python
# ✅ Good: Specific exceptions
class TaskNotFoundError(Exception):
    pass

# ✅ Good: Error context
raise TaskNotFoundError(f"Task {task_id} not found") from e

# ❌ Bad: Generic exceptions
raise Exception("Something went wrong")
```

### Testing
```python
# Test naming: test_<function>_<scenario>
def test_submit_task_creates_pending_task():
    """Test that submit_task creates task with PENDING status"""
    task = submit_task("my_task", [1, 2])
    assert task.status == TaskStatus.PENDING

# Test coverage: ≥ 80% overall
# Critical paths: ≥ 90%
```

---

## Documentation

### Update Docs When:
- Adding new API endpoints
- Changing configuration options
- Adding new features
- Fixing bugs with workarounds

### Documentation Files
- `docs/ARCHITECTURE.md`: System design
- `docs/API_REFERENCE.md`: API endpoints
- `docs/DEPLOYMENT_GUIDE.md`: Deployment instructions
- `docs/MONITORING_GUIDE.md`: Observability setup
- `docs/TROUBLESHOOTING_AND_BEST_PRACTICES.md`: Common issues

### Docs Format
```markdown
# Section Title

**Bold** for emphasis, `code` for code references

## Subsection

1. Numbered lists for steps
2. Each item clear and concise

- Bullet lists for options
- Keep consistent formatting
```

---

## Architecture & Design

### Key Principles
1. **Reliability**: Graceful degradation, circuit breaker patterns
2. **Scalability**: Horizontal scaling, distributed architecture
3. **Observability**: Structured logging, metrics, tracing
4. **Testability**: Comprehensive test coverage, mock-friendly
5. **Maintainability**: Clear code, good documentation

### File Organization
```
src/
  api/               # API layer
    routes/          # Route handlers
    models.py        # Pydantic models
    main.py          # FastAPI app
  core/              # Business logic
    task.py          # Task management
    worker.py        # Worker management
    queue.py         # Queue operations
  resilience/        # Resilience patterns
    circuit_breaker.py
    graceful_degradation.py
    auto_recovery.py
  db/                # Database
    models.py        # SQLAlchemy models
    migrations/      # Alembic migrations
  worker/            # Worker service
    main.py
    executor.py
  monitoring/        # Observability
    metrics.py
    tracing.py
tests/
  unit/              # Unit tests
  integration/       # Integration tests
```

### Adding a New Feature

1. **Create issue** describing feature
2. **Design** (discuss in issue comments)
3. **Create branch**: `feature/feature-name`
4. **Implement**:
   - Add core logic in `src/`
   - Add API endpoint in `src/api/routes/`
   - Add model/schema in `src/api/models.py`
5. **Test**:
   - Unit tests in `tests/unit/`
   - Integration tests in `tests/integration/`
   - Aim for 80%+ coverage
6. **Document**:
   - Update `docs/API_REFERENCE.md`
   - Update README if user-facing
   - Add docstrings to code
7. **Submit PR**
8. **Iterate** on review feedback

---

## Running Tests Locally

### Full Test Suite
```bash
pytest                    # Run all tests
pytest -v               # Verbose output
pytest -x               # Stop on first failure
pytest --tb=short       # Shorter tracebacks
```

### Specific Tests
```bash
# By file
pytest tests/unit/test_tasks.py

# By class
pytest tests/unit/test_tasks.py::TestSubmitTask

# By function
pytest tests/unit/test_tasks.py::TestSubmitTask::test_valid_submission

# By marker
pytest -m "not slow"    # Skip slow tests
```

### Coverage Report
```bash
# Generate coverage
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Watch Mode (TDD)
```bash
# Auto-run tests on file changes
ptw
```

---

## Performance Profiling

### CPU Profiling
```python
from cProfile import Profile
from pstats import Stats

profiler = Profile()
profiler.enable()

# Code to profile
execute_task(task)

profiler.disable()
stats = Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Memory Profiling
```python
from memory_profiler import profile

@profile
def my_function():
    large_list = [i for i in range(1000000)]
    # ... rest of function
```

Run with:
```bash
python -m memory_profiler script.py
```

---

## Reporting Issues

### Issue Checklist
- [ ] Search for existing issues
- [ ] Use clear, descriptive title
- [ ] Include reproducible example
- [ ] Specify Python version, OS
- [ ] Attach logs if applicable
- [ ] Try main branch (if possible)

### Issue Template
```markdown
## Description
Brief description of issue

## Steps to Reproduce
1. ...
2. ...
3. ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Python: 3.9.0
- OS: Ubuntu 20.04
- Version: 1.0.0

## Logs
```
Error message or logs here
```
```

---

## Review Process

### What We Look For
1. **Code Quality**
   - PEP 8 compliance
   - Type hints
   - Clear variable names
   - Appropriate abstractions

2. **Testing**
   - Sufficient test coverage
   - Edge cases covered
   - Integration tests for features

3. **Documentation**
   - Code comments where needed
   - Updated docs
   - Clear commit messages

4. **Performance**
   - No performance regression
   - Efficient algorithms
   - Resource cleanup

5. **Security**
   - Input validation
   - No hardcoded secrets
   - Secure defaults

### Timeline
- Small PRs (< 100 lines): 1-2 days
- Medium PRs (100-500 lines): 2-5 days
- Large PRs (> 500 lines): 5-10 days

---

## Becoming a Maintainer

### Criteria
- 10+ merged PRs
- Active participation in issues/discussions
- Good code quality track record
- Understanding of codebase

### Process
1. Be nominated by existing maintainer
2. Review application by core team
3. Onboarding with existing maintainers
4. Gradual responsibility increase

---

## Communication

### Channels
- **GitHub Issues**: Bug reports, feature requests
- **Discussions**: Questions, ideas
- **Discord**: Real-time chat (link in README)
- **Email**: contact@taskqueue.io

### Code of Conduct
We follow [Contributor Covenant](https://www.contributor-covenant.org/):
- Be respectful and inclusive
- Assume good intent
- Report violations to maintainers

---

## Resources

- **Documentation**: https://docs.taskqueue.io
- **API Reference**: `/docs/API_REFERENCE.md`
- **Architecture**: `/docs/ARCHITECTURE.md`
- **Deployment Guide**: `/docs/DEPLOYMENT_GUIDE.md`

---

## Questions?

- Check existing [GitHub Discussions](https://github.com/taskqueue/discussions)
- Ask in [Discord](https://discord.gg/taskqueue)
- Email: contact@taskqueue.io

**Thank you for contributing! 🎉**
