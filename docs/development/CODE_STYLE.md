# Code Style Guide

> Coding standards, naming conventions, and review process for TaskFlow.

---

## Table of Contents

1. [Python](#python)
2. [TypeScript / React](#typescript--react)
3. [SQL & Database](#sql--database)
4. [Git Conventions](#git-conventions)
5. [Pull Request Template](#pull-request-template)
6. [Code Review Checklist](#code-review-checklist)

---

## Python

### Formatting

| Tool   | Config Location  | Key Settings                               |
| ------ | ---------------- | ------------------------------------------ |
| Black  | `pyproject.toml` | `line-length = 100`                        |
| isort  | `pyproject.toml` | `profile = "black"`                        |
| flake8 | `pyproject.toml` | `max-line-length = 100`                    |
| mypy   | `pyproject.toml` | `strict = false`, `warn_return_any = true` |

Run all formatters:

```bash
black src tests
isort src tests
flake8 src tests
mypy src
```

### Naming Conventions

| Element         | Convention            | Example                      |
| --------------- | --------------------- | ---------------------------- |
| Module          | `snake_case`          | `task_service.py`            |
| Class           | `PascalCase`          | `TaskService`                |
| Function/Method | `snake_case`          | `get_task_by_id()`           |
| Variable        | `snake_case`          | `task_count`                 |
| Constant        | `UPPER_SNAKE_CASE`    | `MAX_RETRIES`                |
| Private         | `_leading_underscore` | `_validate_input()`          |
| Type Variable   | `PascalCase`          | `TaskType`                   |
| Pydantic Model  | `PascalCase` + verb   | `TaskCreate`, `TaskResponse` |

### Import Order

Handled by isort (profile: black). Manual order:

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. Local
from src.models.task import Task
from src.services.task_service import TaskService
```

### Docstrings

Use Google-style docstrings:

```python
def create_task(
    task_data: TaskCreate,
    db: Session,
    current_user: User,
) -> TaskResponse:
    """Create a new task and enqueue it for processing.

    Args:
        task_data: Validated task creation payload.
        db: Database session (injected).
        current_user: Authenticated user (injected).

    Returns:
        The created task with assigned ID and PENDING status.

    Raises:
        HTTPException: 409 if duplicate task name within campaign.
    """
```

### API Route Patterns

```python
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskResponse:
    """Create a new task."""
    ...

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Retrieve a task by ID."""
    ...
```

### Error Handling

```python
# Use HTTPException for API errors
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="Task not found")

# Use structured logging for internal errors
import structlog
logger = structlog.get_logger()

try:
    result = process_task(task)
except Exception as e:
    logger.error("task_processing_failed", task_id=task.id, error=str(e))
    raise
```

### Type Hints

- All function signatures **must** have type hints.
- Use `Optional[T]` or `T | None` for nullable values.
- Use `Annotated[T, ...]` for FastAPI dependency injection.
- Prefer `list[str]` over `List[str]` (Python 3.10+).

---

## TypeScript / React

### Formatting

| Tool       | Config               | Key Settings             |
| ---------- | -------------------- | ------------------------ |
| ESLint     | `eslint.config.js`   | React + TypeScript rules |
| TypeScript | `tsconfig.json`      | `strict: true`           |
| Tailwind   | `tailwind.config.js` | Default + custom theme   |

### Naming Conventions

| Element          | Convention       | Example                  |
| ---------------- | ---------------- | ------------------------ |
| Component        | `PascalCase`     | `TasksPage.tsx`          |
| Hook             | `camelCase`      | `useApi.ts`              |
| Context          | `PascalCase`     | `AuthContext.tsx`        |
| Utility function | `camelCase`      | `formatDate()`           |
| Constant         | `UPPER_SNAKE`    | `API_BASE_URL`           |
| Type/Interface   | `PascalCase`     | `TaskResponse`           |
| CSS class        | Tailwind utility | `className="flex gap-4"` |

### Component Structure

```tsx
// 1. Imports
import { useState, useEffect } from "react";
import { useApi } from "../hooks/useApi";

// 2. Types
interface TaskRowProps {
  task: TaskResponse;
  onRetry: (id: string) => void;
}

// 3. Component
export function TaskRow({ task, onRetry }: TaskRowProps) {
  const [loading, setLoading] = useState(false);

  // 4. Hooks first
  const api = useApi();

  // 5. Handlers
  const handleRetry = async () => {
    setLoading(true);
    await onRetry(task.id);
    setLoading(false);
  };

  // 6. Render
  return (
    <tr>
      <td>{task.name}</td>
      <td>
        <button onClick={handleRetry} disabled={loading}>
          Retry
        </button>
      </td>
    </tr>
  );
}
```

### Testing Conventions

```tsx
// File: ComponentName.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { TaskRow } from "./TaskRow";

describe("TaskRow", () => {
  it("renders task name", () => {
    render(<TaskRow task={mockTask} onRetry={jest.fn()} />);
    expect(screen.getByText("test-task")).toBeInTheDocument();
  });

  it("calls onRetry when button clicked", async () => {
    const onRetry = jest.fn();
    render(<TaskRow task={mockTask} onRetry={onRetry} />);
    fireEvent.click(screen.getByText("Retry"));
    expect(onRetry).toHaveBeenCalledWith("task-1");
  });
});
```

---

## SQL & Database

### Model Conventions

```python
class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="PENDING")
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- Table names: `snake_case`, plural (`tasks`, `workers`, `campaigns`).
- Column names: `snake_case` (`created_at`, `worker_id`).
- Always include `created_at` and `updated_at` timestamps.
- Use Alembic for all schema changes — never modify tables manually.

---

## Git Conventions

### Branch Naming

```
feature/add-task-retry
fix/websocket-reconnect
docs/update-api-reference
refactor/extract-auth-service
test/add-campaign-e2e
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**

| Type       | Usage                                   |
| ---------- | --------------------------------------- |
| `feat`     | New feature                             |
| `fix`      | Bug fix                                 |
| `docs`     | Documentation only                      |
| `test`     | Adding or updating tests                |
| `refactor` | Code change that neither fixes nor adds |
| `perf`     | Performance improvement                 |
| `ci`       | CI/CD pipeline changes                  |
| `chore`    | Build process, tooling, dependencies    |

**Examples:**

```
feat(tasks): add bulk retry endpoint for failed tasks
fix(auth): handle expired refresh token gracefully
docs(api): update OpenAPI spec with new search endpoints
test(campaigns): add integration tests for campaign launch
```

---

## Pull Request Template

```markdown
## Description

Brief description of what this PR does.

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would break existing functionality)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Changes Made

- Change 1
- Change 2

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist

- [ ] Code follows the project's style guide
- [ ] Self-reviewed the code
- [ ] Added docstrings/comments where necessary
- [ ] No new warnings introduced
- [ ] All tests pass locally
```

---

## Code Review Checklist

### Correctness

- [ ] Logic is correct and handles edge cases
- [ ] Error handling is appropriate (no swallowed exceptions)
- [ ] Resource cleanup (DB sessions, file handles) is ensured
- [ ] Concurrency issues addressed (race conditions, deadlocks)

### Security

- [ ] No hardcoded secrets or credentials
- [ ] Input is validated before use
- [ ] SQL queries use parameterized statements (via ORM)
- [ ] Authentication/authorization checks are in place
- [ ] Sensitive data is not logged

### Performance

- [ ] No N+1 query patterns
- [ ] Appropriate database indexes exist
- [ ] Large collections are paginated
- [ ] Expensive operations are cached where sensible

### Maintainability

- [ ] Code is readable without excessive comments
- [ ] Functions are focused (single responsibility)
- [ ] No code duplication that warrants extraction
- [ ] Type hints present on all function signatures
- [ ] Naming is clear and consistent

### Testing

- [ ] Happy path is tested
- [ ] Error/edge cases are tested
- [ ] Mocks are reasonable (not mocking the thing being tested)
- [ ] Test names describe the behavior being verified
