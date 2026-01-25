# API Reference - Distributed Task Queue System

## Overview

RESTful API for the Distributed Task Queue System built with FastAPI.

- **Base URL**: `http://localhost:8000/api/v1`
- **Version**: 1.0.0
- **Authentication**: None (add as needed)

---

## Table of Contents

1. [Tasks API](#tasks-api)
2. [Workers API](#workers-api)
3. [Workflows API](#workflows-api)
4. [Search & Filtering](#search--filtering)
5. [Monitoring APIs](#monitoring-apis)
6. [Resilience API](#resilience-api)
7. [Error Codes](#error-codes)

---

## Tasks API

### Submit Task

**POST** `/tasks`

Submit a new task to the queue.

**Request Body:**

```json
{
  "task_name": "process_payment",
  "task_args": [1234],
  "task_kwargs": {
    "currency": "USD",
    "amount": 99.99
  },
  "priority": 8,
  "queue_name": "payments",
  "max_retries": 3,
  "timeout_seconds": 300,
  "scheduled_at": "2026-01-25T14:30:00Z"
}
```

**Response (201 Created):**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "process_payment",
  "status": "PENDING",
  "priority": 8,
  "created_at": "2026-01-25T14:00:00Z"
}
```

**Query Parameters:**

- `async`: boolean (default: true) - Submit asynchronously

---

### Get Task

**GET** `/tasks/{task_id}`

Retrieve task details and status.

**Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "process_payment",
  "status": "RUNNING",
  "priority": 8,
  "worker_id": "worker-1",
  "created_at": "2026-01-25T14:00:00Z",
  "started_at": "2026-01-25T14:05:00Z",
  "completed_at": null,
  "retry_count": 0,
  "max_retries": 3
}
```

---

### List Tasks

**GET** `/tasks`

List tasks with filtering and pagination.

**Query Parameters:**

- `status`: string - Filter by status (PENDING, RUNNING, COMPLETED, FAILED)
- `priority`: integer - Filter by priority (1-10)
- `queue_name`: string - Filter by queue
- `limit`: integer (default: 50) - Results per page
- `offset`: integer (default: 0) - Pagination offset
- `sort_by`: string (default: created_at) - Sort field
- `sort_order`: string (asc|desc) - Sort order

**Example:**

```bash
GET /api/v1/tasks?status=FAILED&priority=8&limit=10
```

**Response:**

```json
{
  "total": 150,
  "limit": 10,
  "offset": 0,
  "tasks": [...]
}
```

---

### Cancel Task

**POST** `/tasks/{task_id}/cancel`

Cancel a pending or running task.

**Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CANCELLED",
  "message": "Task cancelled successfully"
}
```

---

## Workers API

### Register Worker

**POST** `/workers`

Register a new worker.

**Query Parameters:**

- `hostname`: string - Worker hostname/ID
- `capacity`: integer (default: 5) - Max concurrent tasks

**Response (201 Created):**

```json
{
  "worker_id": "worker-uuid",
  "hostname": "compute-1",
  "status": "ACTIVE",
  "capacity": 5,
  "current_load": 0
}
```

---

### Get Worker Status

**GET** `/workers/{worker_id}/status`

Get detailed worker status.

**Response:**

```json
{
  "worker_id": "worker-uuid",
  "hostname": "compute-1",
  "status": "ACTIVE",
  "capacity": 5,
  "current_load": 3,
  "current_tasks": 3,
  "last_heartbeat": "2026-01-25T14:15:00Z",
  "is_draining": false
}
```

---

### Pause Worker

**PATCH** `/workers/{worker_id}/pause`

Pause a worker (stop accepting new tasks).

**Response:**

```json
{
  "worker_id": "worker-uuid",
  "status": "paused"
}
```

---

### Resume Worker

**PATCH** `/workers/{worker_id}/resume`

Resume a paused worker.

**Response:**

```json
{
  "worker_id": "worker-uuid",
  "status": "resumed"
}
```

---

### Drain Worker

**POST** `/workers/{worker_id}/drain`

Initiate graceful shutdown (finish current tasks then stop).

**Response:**

```json
{
  "worker_id": "worker-uuid",
  "status": "draining"
}
```

---

### Update Worker Capacity

**PATCH** `/workers/{worker_id}/capacity`

Update maximum concurrent tasks.

**Request Body:**

```json
{
  "capacity": 10
}
```

**Response:**

```json
{
  "worker_id": "worker-uuid",
  "capacity": 10
}
```

---

## Search & Filtering

### Advanced Search

**GET** `/search/tasks`

Perform advanced task search with filters.

**Query Parameters:**

- `status`: string - Task status
- `priority`: integer - Task priority
- `task_name`: string - Task function name
- `worker_id`: string - Assigned worker
- `created_after`: datetime - Filter by creation date
- `created_before`: datetime - Filter by creation date
- `search`: string - Full-text search
- `limit`: integer - Results limit
- `offset`: integer - Pagination offset

**Example:**

```bash
GET /api/v1/search/tasks?status=FAILED&created_after=2026-01-24&search=payment&limit=50
```

---

### Filter Presets

**GET** `/search/presets`

Get available filter presets.

**Response:**

```json
{
  "presets": [
    {
      "name": "failed_today",
      "description": "Tasks failed in last 24 hours"
    },
    {
      "name": "high_priority_pending",
      "description": "Priority 8+ PENDING tasks"
    },
    {
      "name": "stuck_tasks",
      "description": "RUNNING for more than 1 hour"
    }
  ]
}
```

---

### Apply Preset

**GET** `/search/presets/{name}`

Apply a filter preset.

**Example:**

```bash
GET /api/v1/search/presets/failed_today
```

---

### Export to CSV

**GET** `/search/tasks/export/csv`

Export filtered tasks to CSV.

**Query Parameters:** (same as search)

**Response:** CSV file download

---

## Monitoring APIs

### System Statistics

**GET** `/dashboard/stats`

Get system-wide statistics.

**Response:**

```json
{
  "queue_depth": 250,
  "active_workers": 5,
  "total_workers": 8,
  "cpu_usage_percent": 45.2,
  "memory_usage_percent": 62.1,
  "total_tasks_submitted": 10000,
  "tasks_completed": 9500,
  "tasks_failed": 450
}
```

---

### Worker Grid

**GET** `/dashboard/workers`

Get status of all workers.

**Response:**

```json
{
  "workers": [
    {
      "worker_id": "worker-1",
      "hostname": "compute-1",
      "status": "ACTIVE",
      "uptime_seconds": 86400,
      "task_rate": 45.2,
      "error_rate": 2.1,
      "capacity_utilization": 0.6
    }
  ]
}
```

---

### Task Analytics

**GET** `/analytics/trends`

Get task execution trends.

**Query Parameters:**

- `hours`: integer (default: 24) - Time period
- `interval`: string (hourly|daily) - Aggregation interval

**Response:**

```json
{
  "completion_rate": 95.5,
  "average_wait_time_seconds": 12.3,
  "peak_loads": ["14:00", "15:30"],
  "failure_patterns": [
    {
      "error": "Timeout",
      "count": 45,
      "percentage": 10.0
    }
  ]
}
```

---

### Alerts

**GET** `/alerts`

Get active alerts.

**Response:**

```json
{
  "alerts": [
    {
      "alert_id": "alert-uuid",
      "type": "HIGH_QUEUE_DEPTH",
      "severity": "WARNING",
      "description": "Queue depth exceeded 1000",
      "created_at": "2026-01-25T14:00:00Z",
      "acknowledged": false
    }
  ]
}
```

---

## Resilience API

### Mark Service Degraded

**POST** `/resilience/degradation/mark`

Mark a service as degraded.

**Request Body:**

```json
{
  "service_name": "database",
  "strategy": "return_cached",
  "duration_seconds": 300
}
```

---

### Get Resilience Summary

**GET** `/resilience/summary`

Get overall system resilience status.

**Response:**

```json
{
  "system_health": {
    "components_total": 5,
    "healthy": 4,
    "unhealthy": 1
  },
  "degradation": {
    "degraded_services_count": 1,
    "services": ["database"]
  },
  "resilience_score": 80.0
}
```

---

### Health Check

**GET** `/health`

System-wide health check.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "workers": "healthy"
  }
}
```

---

## Debug & Troubleshooting

### Replay Task

**POST** `/tasks/{task_id}/replay`

Replay a failed task.

**Response:**

```json
{
  "task_id": "new-task-uuid",
  "status": "PENDING",
  "original_task_id": "original-uuid"
}
```

---

### Get Task Timeline

**GET** `/tasks/{task_id}/timeline`

Get detailed execution timeline.

**Response:**

```json
{
  "task_id": "task-uuid",
  "task_name": "process_data",
  "status": "COMPLETED",
  "created_at": "2026-01-25T14:00:00Z",
  "started_at": "2026-01-25T14:05:00Z",
  "completed_at": "2026-01-25T14:10:00Z",
  "duration_seconds": 300,
  "events": [
    {
      "timestamp": "2026-01-25T14:05:00Z",
      "event_type": "started",
      "details": { "worker_id": "worker-1" }
    }
  ]
}
```

---

### Compare Tasks

**GET** `/tasks/{task_id1}/compare/{task_id2}`

Compare two task executions.

**Response:**

```json
{
  "same_function": true,
  "same_args": false,
  "same_priority": true,
  "timing": {
    "task1_duration": 30,
    "task2_duration": 45
  }
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Meaning                                |
| ---- | -------------------------------------- |
| 200  | OK - Success                           |
| 201  | Created - Resource created             |
| 204  | No Content - Success, no body          |
| 400  | Bad Request - Invalid parameters       |
| 401  | Unauthorized - Authentication required |
| 403  | Forbidden - Access denied              |
| 404  | Not Found - Resource not found         |
| 409  | Conflict - Resource conflict           |
| 429  | Too Many Requests - Rate limited       |
| 500  | Internal Server Error                  |
| 503  | Service Unavailable                    |

### Error Response Format

```json
{
  "detail": "Task not found",
  "code": "TASK_NOT_FOUND",
  "request_id": "req-uuid",
  "timestamp": "2026-01-25T14:00:00Z"
}
```

---

## Rate Limiting

- **Default**: 1000 requests/minute per IP
- **Headers**:
  - `X-RateLimit-Limit`: Rate limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

---

## Pagination

All list endpoints support pagination:

**Request:**

```bash
GET /api/v1/tasks?limit=50&offset=0
```

**Response:**

```json
{
  "total": 500,
  "limit": 50,
  "offset": 0,
  "data": [...]
}
```

---

## OpenAPI/Swagger Documentation

Access interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Webhooks (Future)

Coming in v1.1:

- Task completion notifications
- Error notifications
- Custom event subscriptions
