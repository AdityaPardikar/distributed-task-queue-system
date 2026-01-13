"""CONTRIBUTING.md - Development guidelines"""

# Contributing to TaskFlow

## Development Setup

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Git

### Quick Start

1. **Clone and setup**

```bash
git clone <repo>
cd taskflow
python scripts/setup_dev.py
```

2. **Start services**

```bash
docker-compose -f docker-compose.local.yml up -d
```

3. **Run API**

```bash
python run.py
```

## Commit Guidelines

- Follow semantic commits: `type(scope): message`
- Types: feat, fix, docs, style, refactor, test, chore
- Examples:
  - `feat(broker): implement priority queue logic`
  - `fix(worker): handle task timeout gracefully`
  - `test(api): add task submission tests`

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src

# Specific test
pytest tests/unit/test_broker.py -v
```

## Code Quality

```bash
# Format code
black src tests

# Lint
flake8 src tests

# Type check
mypy src
```

## Project Structure

- `src/api/` - FastAPI endpoints
- `src/core/` - Core queue logic (broker, coordinator, worker)
- `src/models/` - SQLAlchemy models
- `src/services/` - Business logic
- `src/tasks/` - Task definitions
- `tests/` - Test suite
- `deployment/` - Docker & deployment configs
