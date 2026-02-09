# API Documentation & Developer Guide

## Table of Contents

- [API Overview](#api-overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
- [Webhooks](#webhooks)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## API Overview

The Distributed Task Queue System provides a comprehensive RESTful API for managing distributed task processing, worker management, analytics, and system monitoring.

**API Version:** v1
**Base Path:** `/api/v1`

## Authentication

Currently, the API supports multiple authentication methods:

### API Key Authentication

Include API key in the request header:

```
X-API-Key: your-api-key-here
```

### Bearer Token

Include JWT token in Authorization header:

```
Authorization: Bearer <jwt-token>
```

## Base URL

```
Development:  http://localhost:5000/api/v1
Production:   https://api.yourdomain.com/api/v1
```

## Response Format

### Success Response

```json
{
  "status": "success",
  "data": {
    "id": "task-123",
    "name": "Example Task",
    "status": "completed"
  },
  "timestamp": "2024-02-09T10:30:00Z"
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid task ID",
    "details": {
      "field": "task_id",
      "reason": "Not a valid UUID"
    }
  },
  "timestamp": "2024-02-09T10:30:00Z"
}
```

## Error Handling

### HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `204 No Content` - Successful request with no response body
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

### Common Error Codes

```
INVALID_REQUEST        - Request validation failed
UNAUTHORIZED          - Authentication failed
FORBIDDEN             - Permission denied
NOT_FOUND             - Resource not found
CONFLICT              - Resource conflict
RATE_LIMITED          - Too many requests
INTERNAL_ERROR        - Server error
SERVICE_UNAVAILABLE   - Service temporarily down
```

## Health Endpoints

### GET /health

Check basic health status

```bash
curl http://localhost:5000/health
```

Response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-02-09T10:30:00Z"
}
```

### GET /ready

Check service readiness (all dependencies)

```bash
curl http://localhost:5000/ready
```

Response:

```json
{
  "status": "ready",
  "version": "1.0.0",
  "timestamp": "2024-02-09T10:30:00Z"
}
```

### GET /info

Get application information

```bash
curl http://localhost:5000/info
```

Response:

```json
{
  "name": "Distributed Task Queue System",
  "version": "1.0.0",
  "environment": "production",
  "debug": false
}
```

## Task Management Endpoints

### GET /tasks

List all tasks

```bash
curl -X GET http://localhost:5000/api/v1/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

Query Parameters:

- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 50, max: 100)
- `status`: Filter by status (pending, running, completed, failed)
- `priority`: Filter by priority (low, medium, high)
- `worker_id`: Filter by worker assignment
- `sort`: Sort field (created_at, updated_at, duration)
- `order`: Sort order (asc, desc)

### GET /tasks/{task_id}

Get task details

```bash
curl http://localhost:5000/api/v1/tasks/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer <token>"
```

### POST /tasks

Create a new task

```bash
curl -X POST http://localhost:5000/api/v1/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Process Data",
    "description": "Process CSV file",
    "priority": "high",
    "payload": {
      "file_path": "/data/input.csv"
    }
  }'
```

Request Body:

```json
{
  "name": "string",
  "description": "string",
  "priority": "low|medium|high",
  "retry_count": 0,
  "timeout": 3600,
  "payload": {}
}
```

### PUT /tasks/{task_id}

Update task

```bash
curl -X PUT http://localhost:5000/api/v1/tasks/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "cancelled"
  }'
```

### DELETE /tasks/{task_id}

Delete task

```bash
curl -X DELETE http://localhost:5000/api/v1/tasks/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer <token>"
```

## Worker Management Endpoints

### GET /workers

List all workers

```bash
curl http://localhost:5000/api/v1/workers \
  -H "Authorization: Bearer <token>"
```

Query Parameters:

- `status`: Filter by status (active, inactive)
- `skip`: Pagination skip
- `limit`: Pagination limit

### GET /workers/{worker_id}

Get worker details

```bash
curl http://localhost:5000/api/v1/workers/worker-001 \
  -H "Authorization: Bearer <token>"
```

### POST /workers/heartbeat

Update worker heartbeat (called by workers)

```bash
curl -X POST http://localhost:5000/api/v1/workers/heartbeat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "worker-001",
    "status": "active",
    "current_load": 5,
    "max_capacity": 10
  }'
```

### GET /workers/status

Get all workers health status

```bash
curl http://localhost:5000/workers/status \
  -H "Authorization: Bearer <token>"
```

## Analytics Endpoints

### GET /analytics/dashboard

Get dashboard metrics

```bash
curl http://localhost:5000/api/v1/analytics/dashboard \
  -H "Authorization: Bearer <token>"
```

Response:

```json
{
  "total_tasks": 1500,
  "completed_tasks": 1200,
  "failed_tasks": 50,
  "pending_tasks": 250,
  "completion_rate": 0.8,
  "average_duration": 45.5,
  "workers_active": 5,
  "workers_total": 10
}
```

### GET /analytics/trends

Get performance trends

```bash
curl http://localhost:5000/api/v1/analytics/trends \
  -H "Authorization: Bearer <token>"
```

Query Parameters:

- `days`: Number of days to include (default: 7, max: 365)
- `metric`: Metric type (completion_rate, avg_duration, error_rate)

## WebSocket Endpoints

### ws://localhost:5000/ws/metrics

Subscribe to real-time metrics updates

```javascript
const ws = new WebSocket("ws://localhost:5000/ws/metrics", {
  headers: {
    Authorization: "Bearer <token>",
  },
});

ws.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  console.log("Updated metrics:", metrics);
};
```

### ws://localhost:5000/ws/tasks

Subscribe to task status updates

```javascript
const ws = new WebSocket("ws://localhost:5000/ws/tasks", {
  headers: {
    Authorization: "Bearer <token>",
  },
});

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log("Task update:", update);
};
```

## Examples

### Create and Monitor Task

```bash
# Create task
TASK=$(curl -X POST http://localhost:5000/api/v1/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Processing",
    "priority": "high"
  }' | jq -r '.data.id')

echo "Created task: $TASK"

# Poll task status
while true; do
  STATUS=$(curl http://localhost:5000/api/v1/tasks/$TASK \
    -H "Authorization: Bearer <token>" | jq -r '.data.status')

  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi

  sleep 2
done
```

### Export Analytics Data

```bash
# Export to JSON
curl http://localhost:5000/api/v1/analytics/export \
  -H "Authorization: Bearer <token>" \
  -H "Accept: application/json" \
  -o analytics-export.json

# Export to CSV
curl http://localhost:5000/api/v1/analytics/export \
  -H "Authorization: Bearer <token>" \
  -H "Accept: text/csv" \
  -o analytics-export.csv
```

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Standard: 1000 requests per hour per API key**
- **Burst: 100 requests per minute per API key**

Rate limit headers:

- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Pagination

List endpoints support pagination:

```bash
curl "http://localhost:5000/api/v1/tasks?skip=0&limit=10" \
  -H "Authorization: Bearer <token>"
```

Response includes pagination metadata:

```json
{
  "data": [...],
  "pagination": {
    "skip": 0,
    "limit": 10,
    "total": 150,
    "pages": 15
  }
}
```

## Testing API

### Using cURL

```bash
# Get bearer token
TOKEN=$(curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' | jq -r '.token')

# Use token in requests
curl http://localhost:5000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN"
```

### Using Postman

1. Import [Postman collection](./postman-collection.json)
2. Set environment variables:
   - `base_url`: http://localhost:5000/api/v1
   - `token`: Bearer token from login endpoint
3. Run requests from collection

### Using Python

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"
TOKEN = "your-bearer-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Get tasks
response = requests.get(f"{BASE_URL}/tasks", headers=HEADERS)
tasks = response.json()["data"]

# Create task
payload = {
    "name": "New Task",
    "priority": "high"
}
response = requests.post(f"{BASE_URL}/tasks", json=payload, headers=HEADERS)
task = response.json()["data"]
```

## Swagger/OpenAPI Documentation

Interactive API documentation is available at:

```
http://localhost:5000/docs          # Swagger UI
http://localhost:5000/redoc         # ReDoc
http://localhost:5000/openapi.json  # OpenAPI schema
```
