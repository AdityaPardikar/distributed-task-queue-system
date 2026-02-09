# Testing Guide & Quality Assurance

## Table of Contents

- [Test Structure](#test-structure)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [E2E Testing](#e2e-testing)
- [Performance Testing](#performance-testing)
- [Security Testing](#security-testing)
- [Coverage Goals](#coverage-goals)
- [Running Tests](#running-tests)
- [CI/CD Integration](#cicd-integration)

## Test Structure

```
project/
├── tests/                    # Backend tests
│   ├── conftest.py          # Pytest configuration
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── frontend/
│   └── src/
│       └── **/__tests__/    # Frontend tests
└── scripts/
    ├── run-tests.sh         # Test runner
    └── coverage-report.sh   # Coverage analysis
```

## Unit Testing

### Backend Unit Tests

Unit tests for individual functions and classes.

```python
# tests/unit/test_tasks.py
import pytest
from src.models import Task
from src.services import TaskService

@pytest.fixture
def task_service(db):
    return TaskService(db)

def test_create_task(task_service):
    """Test task creation"""
    task = task_service.create_task(
        name="Test Task",
        priority="high"
    )
    assert task.id is not None
    assert task.name == "Test Task"

def test_task_validation(task_service):
    """Test task validation"""
    with pytest.raises(ValueError):
        task_service.create_task(
            name="",  # Invalid: empty name
            priority="invalid"
        )
```

### Frontend Unit Tests

Unit tests for React components and utilities.

```javascript
// frontend/src/__tests__/components/TaskCard.test.tsx
import { render, screen } from "@testing-library/react";
import TaskCard from "@/components/TaskCard";

describe("TaskCard", () => {
  it("renders task information", () => {
    const task = {
      id: "123",
      name: "Test Task",
      status: "completed",
    };

    render(<TaskCard task={task} />);

    expect(screen.getByText("Test Task")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });
});
```

## Integration Testing

### Backend Integration Tests

Tests that verify interaction between multiple components.

```python
# tests/integration/test_task_workflow.py
def test_task_lifecycle(client, db):
    """Test complete task lifecycle from creation to completion"""

    # Create task
    response = client.post('/api/v1/tasks', json={
        'name': 'Integration Test Task',
        'priority': 'high'
    })
    assert response.status_code == 201
    task_id = response.json()['data']['id']

    # Assign to worker
    response = client.post(f'/api/v1/tasks/{task_id}/assign', json={
        'worker_id': 'worker-1'
    })
    assert response.status_code == 200

    # Complete task
    response = client.post(f'/api/v1/tasks/{task_id}/complete', json={
        'result': {'status': 'success'}
    })
    assert response.status_code == 200
```

### Frontend Integration Tests

Tests that verify multiple components working together.

```javascript
// frontend/src/__tests__/integration/TaskFlow.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TaskDashboard from "@/pages/TaskDashboard";

describe("Task Management Flow", () => {
  it("allows creating and completing a task", async () => {
    const user = userEvent.setup();
    render(<TaskDashboard />);

    // Create task
    const createBtn = screen.getByText("Create Task");
    await user.click(createBtn);

    const input = screen.getByPlaceholderText("Task name");
    await user.type(input, "Integration Test");

    const submitBtn = screen.getByRole("button", { name: /submit/i });
    await user.click(submitBtn);

    // Verify task created
    await waitFor(() => {
      expect(screen.getByText("Integration Test")).toBeInTheDocument();
    });
  });
});
```

## E2E Testing

### Playwright Tests

Full user workflow testing.

```javascript
// e2e/task-management.spec.ts
import { test, expect } from "@playwright/test";

test("complete task management workflow", async ({ page }) => {
  // Login
  await page.goto("http://localhost:3000/login");
  await page.fill("[data-test=email]", "user@example.com");
  await page.fill("[data-test=password]", "password");
  await page.click("[data-test=login-button]");

  // Wait for dashboard
  await page.waitForURL("**/dashboard");

  // Create task
  await page.click("[data-test=new-task]");
  await page.fill("[data-test=task-name]", "E2E Test Task");
  await page.selectOption("[data-test=priority]", "high");
  await page.click("[data-test=create-button]");

  // Verify task appears
  await expect(page.locator("text=E2E Test Task")).toBeVisible();
});
```

## Performance Testing

### Load Testing with k6

```javascript
// scripts/load-test.js
import http from "k6/http";
import { check, sleep } from "k6";

export let options = {
  vus: 10, // Virtual users
  duration: "30s", // Test duration
  thresholds: {
    http_req_duration: ["p(95)<500"], // 95% requests under 500ms
    http_req_failed: ["rate<0.1"], // Less than 10% failure rate
  },
};

export default function () {
  // Test task creation
  let response = http.post(
    "http://localhost:5000/api/v1/tasks",
    {
      name: "Load Test Task",
      priority: "medium",
    },
    {
      headers: {
        Authorization: `Bearer ${__ENV.TOKEN}`,
      },
    },
  );

  check(response, {
    "status is 201": (r) => r.status === 201,
    "response time < 500ms": (r) => r.timings.duration < 500,
  });

  sleep(1);
}
```

Run load test:

```bash
k6 run scripts/load-test.js
```

### Database Query Performance

```python
# tests/performance/test_query_performance.py
def test_list_tasks_performance(db):
    """Test that task listing performs well with large datasets"""
    from time import time

    # Create 1000 tasks
    for i in range(1000):
        Task.create(name=f"Task {i}", status="completed")

    # Measure query time
    start = time()
    tasks = Task.query.limit(50).all()
    elapsed = time() - start

    # Should complete in < 100ms
    assert elapsed < 0.1, f"Query took {elapsed}s, expected < 0.1s"
```

## Security Testing

### OWASP Top 10 Checklist

#### A1: Injection

```python
def test_sql_injection_protection(client):
    """Verify SQL injection is prevented"""
    response = client.get(
        '/api/v1/tasks',
        params={'search': "'; DROP TABLE tasks; --"}
    )
    assert response.status_code == 200
    # Verify table still exists
    assert Task.query.count() > 0
```

#### A2: Authentication

```python
def test_authentication_required(client):
    """Verify authentication is required"""
    response = client.get('/api/v1/tasks')
    assert response.status_code == 401

def test_invalid_token_rejected(client):
    """Verify invalid tokens are rejected"""
    response = client.get(
        '/api/v1/tasks',
        headers={'Authorization': 'Bearer invalid-token'}
    )
    assert response.status_code == 401
```

#### A3: Sensitive Data Exposure

```python
def test_passwords_not_exposed(client, user):
    """Verify passwords are never exposed"""
    response = client.get(f'/api/v1/users/{user.id}')
    data = response.json()
    assert 'password' not in data
    assert 'password_hash' not in data
```

#### A6: XSS Prevention

```javascript
// frontend/__tests__/security/xss-prevention.test.ts
describe("XSS Prevention", () => {
  it("escapes HTML in user input", () => {
    const malicious = '<img src=x onerror="alert(1)">';
    render(<TaskCard task={{ name: malicious }} />);

    // Verify script doesn't execute and HTML is escaped
    expect(screen.queryByText(/alert/i)).not.toBeInTheDocument();
  });
});
```

### CSRF Protection

```python
def test_csrf_token_validated(client):
    """Verify CSRF token is required for state-changing operations"""
    response = client.post('/api/v1/tasks', json={'name': 'Test'})
    assert response.status_code == 403  # CSRF token missing
```

## Coverage Goals

### Target Coverage: >80%

```bash
# Backend coverage
pytest --cov=src --cov-report=html tests/

# Frontend coverage
npm test -- --coverage --watchAll=false

# View HTML report
open htmlcov/index.html
open coverage/lcov-report/index.html
```

### Coverage by Module

- Core Models: 95%+
- Services: 85%+
- API Routes: 80%+
- Frontend Components: 80%+
- Utilities: 90%+

## Running Tests

### Backend Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/unit/test_tasks.py

# Specific test
pytest tests/unit/test_tasks.py::test_create_task

# With coverage
pytest --cov=src tests/

# With verbose output
pytest -v tests/

# Run only failed tests
pytest --lf tests/

# Run tests matching pattern
pytest -k "task" tests/
```

### Frontend Tests

```bash
# All tests
npm test -- --watchAll=false

# Watch mode
npm test

# Specific file
npm test -- TaskCard.test.tsx

# Coverage
npm test -- --coverage --watchAll=false

# Update snapshots
npm test -- -u
```

### Integration Tests

```bash
# Run with docker-compose
docker-compose exec backend pytest tests/integration/

# Or locally with running services
pytest tests/integration/
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest --cov=src --cov-report=xml tests/

      - name: Upload coverage
        uses: codecov/codecov-action@v2

  frontend:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Node
        uses: actions/setup-node@v2
        with:
          node-version: 18

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run tests
        run: cd frontend && npm test -- --coverage --watchAll=false

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Reporting

### Generate Test Report

```bash
# HTML report
pytest --html=report.html tests/

# JUnit XML for CI systems
pytest --junit-xml=junit.xml tests/

# Coverage report
pytest --cov=src --cov-report=html tests/
```

### View Reports Locally

```bash
# Open test report
open report.html

# Open coverage report
open htmlcov/index.html
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names should describe what they test
3. **Speed**: Keep tests fast (< 100ms per unit test)
4. **Coverage**: Aim for >80% code coverage
5. **Mocking**: Mock external dependencies
6. **Setup/Teardown**: Use fixtures for common setup
7. **DRY**: Extract common test patterns into fixtures
8. **Documentation**: Document complex test scenarios
9. **Assertions**: Use clear, specific assertions
10. **Review**: Review tests during code review

## Accessibility Testing

### Automated Accessibility Tests

```javascript
// frontend/__tests__/accessibility.test.ts
import { render } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import Dashboard from "@/pages/Dashboard";

expect.extend(toHaveNoViolations);

describe("Accessibility", () => {
  it("has no accessibility violations", async () => {
    const { container } = render(<Dashboard />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```
