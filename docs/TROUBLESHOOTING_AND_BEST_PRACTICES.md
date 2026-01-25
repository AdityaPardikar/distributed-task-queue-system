# Troubleshooting & Best Practices Guide

## Overview
Common issues, solutions, and best practices for operating the Distributed Task Queue System.

---

## Table of Contents
1. [Common Issues & Solutions](#common-issues--solutions)
2. [Performance Optimization](#performance-optimization)
3. [Best Practices](#best-practices)
4. [FAQ](#faq)

---

## Common Issues & Solutions

### Issue: Queue Depth Growing Unbounded
**Problem**: `task_queue:queue_depth` continuously increasing

**Root Causes**:
1. Workers not processing tasks
2. Task execution too slow
3. Worker failures
4. Infrastructure saturation

**Diagnosis Steps**:
```bash
# 1. Check queue depth
curl http://localhost:8000/api/v1/dashboard/queue-depth

# 2. Check submission vs completion rate
curl http://localhost:8000/api/v1/dashboard/stats
# Compare: submissions/min vs completions/min

# 3. Check active workers
curl http://localhost:8000/api/v1/workers/status/all
# Expected: status="active" for most workers

# 4. Check for stuck tasks (RUNNING > 1 hour)
curl "http://localhost:8000/api/v1/search/presets/stuck_tasks"
```

**Solutions** (in priority order):
1. **Scale workers**: Add more worker instances
   ```bash
   docker-compose up -d --scale worker=10
   ```

2. **Increase worker capacity**:
   ```bash
   WORKER_CONCURRENCY=10 python -m src.worker.main
   ```

3. **Optimize task execution**:
   - Profile slow tasks
   - Reduce memory/CPU per task
   - Use caching where possible

4. **Check for failed tasks**:
   ```bash
   curl "http://localhost:8000/api/v1/tasks?status=FAILED&limit=100"
   ```

5. **Emergency: Drain non-critical tasks**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/search/tasks/bulk-action \
     -H "Content-Type: application/json" \
     -d '{
       "action": "cancel",
       "filters": {"priority": 1}
     }'
   ```

---

### Issue: High Task Failure Rate
**Problem**: Tasks failing at > 5% rate

**Root Causes**:
1. Invalid task arguments
2. External service unavailable
3. Insufficient resources
4. Code bugs

**Diagnosis Steps**:
```bash
# 1. Get failure statistics
curl http://localhost:8000/api/v1/analytics/trends

# 2. Find failed tasks
curl "http://localhost:8000/api/v1/search/tasks?status=FAILED&limit=20"

# 3. Get specific task error
curl http://localhost:8000/api/v1/tasks/{task_id}
# Look for: error_message, traceback fields

# 4. Check for patterns
curl "http://localhost:8000/api/v1/search/tasks?task_name=process_payment&status=FAILED"

# 5. Check worker logs
docker logs worker-container | grep ERROR
```

**Solutions**:
1. **Fix invalid arguments**:
   - Validate input schema
   - Add input sanitization
   - Document required fields

2. **Retry transient failures**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/replay
   ```

3. **Check external services**:
   ```bash
   # Test API connectivity
   curl -i https://external-api.example.com/health
   
   # Check DNS
   nslookup external-api.example.com
   ```

4. **Add circuit breaker for external calls**:
   ```python
   circuit = CircuitBreaker("external_api", failure_threshold=5)
   result = circuit.call(call_external_api, args)
   ```

5. **Increase retry limits** (for transient errors):
   ```python
   task = Task(
       name="process_payment",
       args=[...],
       max_retries=5,  # Default: 3
       retry_delay_seconds=10
   )
   ```

---

### Issue: Worker Not Processing Tasks
**Problem**: Worker registered but no tasks assigned

**Root Causes**:
1. Worker at capacity
2. Worker unhealthy
3. No matching tasks
4. Network/connectivity issues

**Diagnosis Steps**:
```bash
# 1. Check worker status
curl http://localhost:8000/api/v1/workers/{worker_id}/status

# 2. Check worker capacity vs load
# Response: current_load vs capacity
# Should have: current_load < capacity

# 3. Check worker health
curl http://localhost:8000/api/v1/resilience/health/worker-{id}

# 4. Check for tasks in queue
curl "http://localhost:8000/api/v1/tasks?status=PENDING&limit=5"

# 5. Check worker logs
docker logs worker-container
```

**Solutions**:
1. **Reduce worker load**:
   ```bash
   # Check current tasks
   curl http://localhost:8000/api/v1/workers/{worker_id}/status
   
   # Cancel non-critical tasks
   curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/cancel
   ```

2. **Restart worker**:
   ```bash
   docker restart worker-container
   ```

3. **Increase worker capacity**:
   ```bash
   WORKER_CONCURRENCY=20 python -m src.worker.main
   ```

4. **Check queue name match**:
   ```bash
   # Task queue name must match worker queue name
   Task(name="task", queue_name="payments")  # Task subscribes to "payments"
   Worker(queue_name="payments")             # Worker listens to "payments"
   ```

---

### Issue: Database Connection Pool Exhausted
**Problem**: "too many connections" errors in logs

**Root Causes**:
1. Connection leak (not closing connections)
2. Slow queries holding connections
3. Insufficient pool size
4. Database timeout too long

**Diagnosis Steps**:
```bash
# 1. Check connection pool
curl http://localhost:8000/api/v1/health/database

# 2. Check PostgreSQL connections
psql -U postgres -d taskqueue -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Find long-running queries
psql -U postgres -d taskqueue -c "
  SELECT now() - query_start, query 
  FROM pg_stat_activity 
  WHERE query !~ 'autovacuum' 
  ORDER BY query_start;"

# 4. Check for idle connections
psql -U postgres -d taskqueue -c "
  SELECT state, count(*) 
  FROM pg_stat_activity 
  GROUP BY state;"
```

**Solutions**:
1. **Increase connection pool**:
   ```bash
   DATABASE_POOL_SIZE=40 python -m src.api.main
   ```

2. **Reduce connection timeout**:
   ```bash
   DATABASE_POOL_TIMEOUT=10 python -m src.api.main
   ```

3. **Kill idle connections**:
   ```sql
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE state = 'idle' 
   AND query_start < now() - interval '1 hour';
   ```

4. **Optimize slow queries**:
   ```bash
   # Find slow queries
   psql -U postgres -d taskqueue -c "
    SELECT mean_exec_time, query 
    FROM pg_stat_statements 
    ORDER BY mean_exec_time DESC 
    LIMIT 10;"
   
   # Add indexes as needed
   ```

5. **Enable connection pooling** (PgBouncer):
   ```ini
   [databases]
   taskqueue = host=localhost port=5432 dbname=taskqueue
   
   [pgbouncer]
   pool_mode = transaction
   max_client_conn = 1000
   default_pool_size = 25
   ```

---

### Issue: Redis Memory Full
**Problem**: Redis OOM or eviction errors

**Root Causes**:
1. Unbounded cache growth
2. Memory leak in data structures
3. Insufficient memory allocation
4. Poor TTL configuration

**Diagnosis Steps**:
```bash
# 1. Check Redis memory
redis-cli info memory

# 2. Get top keys by memory
redis-cli --bigkeys

# 3. Check memory by type
redis-cli --memkeys

# 4. Check eviction policy
redis-cli config get maxmemory-policy
```

**Solutions**:
1. **Increase Redis memory**:
   ```bash
   # In docker-compose.yml
   redis:
     command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
   ```

2. **Reduce TTL on keys**:
   ```python
   # Shorter TTL for temporary data
   cache.set(key, value, ttl=300)  # 5 minutes
   ```

3. **Clear old data**:
   ```bash
   # Clear by key pattern
   redis-cli EVAL "return redis.call('del', unpack(redis.call('keys', ARGV[1])))" 0 "recovery:*:*"
   ```

4. **Use key scanning** instead of KEYS:
   ```python
   cursor = 0
   while True:
       cursor, keys = redis.scan(cursor, match="recovery:*", count=100)
       for key in keys:
           redis.delete(key)
       if cursor == 0:
           break
   ```

---

## Performance Optimization

### Database Optimization

#### Index Strategy
```sql
-- Task lookups by status (most common)
CREATE INDEX CONCURRENTLY idx_task_status ON tasks(status);

-- Queue operations by created_at
CREATE INDEX CONCURRENTLY idx_task_created ON tasks(created_at DESC);

-- Priority queue ordering
CREATE INDEX CONCURRENTLY idx_task_priority 
  ON tasks(status, priority DESC, created_at ASC) 
  WHERE status = 'PENDING';

-- Scheduled task lookups
CREATE INDEX CONCURRENTLY idx_task_scheduled 
  ON tasks(scheduled_at) 
  WHERE status = 'PENDING' AND scheduled_at IS NOT NULL;

-- Worker lookups by status
CREATE INDEX CONCURRENTLY idx_worker_status ON workers(status);

-- Worker heartbeat tracking
CREATE INDEX CONCURRENTLY idx_worker_heartbeat 
  ON workers(last_heartbeat DESC);
```

#### Query Optimization
```python
# ❌ Bad: N+1 queries
tasks = Task.query.all()
for task in tasks:
    worker = Worker.query.get(task.worker_id)  # N queries!

# ✅ Good: Eager loading
tasks = Task.query.joinedload(Task.worker).all()

# ❌ Bad: Loading all data
tasks = Task.query.limit(100)

# ✅ Good: Select only needed columns
tasks = db.session.query(Task.id, Task.status, Task.created_at).limit(100)

# ❌ Bad: IN with many values
Task.query.filter(Task.id.in_(big_list))

# ✅ Good: Batch processing
for batch in chunks(big_list, 1000):
    Task.query.filter(Task.id.in_(batch))
```

#### Connection Pooling
```python
# Configure in config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,           # Base pool size
    "max_overflow": 10,        # Additional connections if needed
    "pool_recycle": 3600,      # Recycle connections after 1 hour
    "echo_pool": False,        # Don't log pool operations
}
```

### Redis Optimization

#### Key Design
```python
# ❌ Bad: Long keys, poor structure
key = f"recovery_attempt_{task_id}_attempt_{attempt_num}_timestamp_{ts}"

# ✅ Good: Structured, short keys
key = f"recovery:{task_id}:attempts"  # Using hash instead

# Use Redis data structures efficiently
redis.hset(f"recovery:{task_id}", mapping={
    "attempts": 3,
    "last_attempt": 1234567890,
    "next_retry": 1234567900
})
```

#### Pipeline Operations
```python
# ❌ Bad: Multiple network roundtrips
redis.set(key1, val1)
redis.set(key2, val2)
redis.get(key1)

# ✅ Good: Single roundtrip with pipeline
pipe = redis.pipeline()
pipe.set(key1, val1)
pipe.set(key2, val2)
pipe.get(key1)
pipe.execute()
```

### API Response Optimization

#### Pagination
```python
# Always limit results
@app.get("/tasks")
def list_tasks(skip: int = 0, limit: int = 100):
    if limit > 1000:
        limit = 1000  # Cap maximum limit
    
    return Task.query.offset(skip).limit(limit).all()
```

#### Caching
```python
# Cache expensive queries
@cached(timeout=300)
def get_queue_depth():
    return Task.query.filter_by(status='PENDING').count()

# Cache API responses
@app.get("/analytics/trends")
def get_trends(cache: CacheControl = CacheControl(max_age=60)):
    return compute_trends()
```

### Worker Optimization

#### Task Batching
```python
# Process multiple tasks together
def batch_process_tasks(worker_id: str, batch_size: int = 10):
    tasks = get_assigned_tasks(worker_id, limit=batch_size)
    
    results = []
    for task in tasks:
        try:
            result = execute_task(task)
            results.append(result)
        except Exception as e:
            handle_task_failure(task, e)
    
    return results
```

#### Resource Management
```python
# Monitor memory usage
import psutil

def check_resource_limits():
    process = psutil.Process()
    memory_percent = process.memory_percent()
    
    if memory_percent > 80:
        # Reduce worker concurrency
        pause_new_task_assignments()
    elif memory_percent < 50:
        # Increase worker concurrency
        resume_task_assignments()
```

---

## Best Practices

### 1. Task Design
```python
# ✅ Good: Idempotent, stateless tasks
@task
def send_email(user_id: int, email: str):
    """Idempotent: Safe to retry multiple times"""
    # Check if already sent (idempotency key)
    if EmailLog.query.filter_by(user_id=user_id, email=email).exists():
        return {"status": "already_sent"}
    
    # Send email
    send_to(email)
    
    # Log
    EmailLog.create(user_id=user_id, email=email)
    return {"status": "sent"}

# ❌ Bad: Non-idempotent, side-effecting
def charge_credit_card(user_id: int, amount: float):
    """Will charge multiple times if retried!"""
    charge_card(user_id, amount)
    return {"status": "charged"}
```

### 2. Error Handling
```python
# ✅ Good: Specific exception handling
@task
def process_payment(payment_id: int):
    try:
        validate_payment(payment_id)
        charge_card(payment_id)
        send_receipt(payment_id)
    except PaymentDeclinedError as e:
        # Specific: Don't retry
        log_declined_payment(payment_id, e)
        return {"status": "failed", "reason": "declined"}
    except TemporaryNetworkError as e:
        # Transient: Will retry
        raise  # Let queue retry
    except Exception as e:
        # Unknown: Log and fail safe
        log_error(f"Unexpected error: {e}")
        raise

# ❌ Bad: Catch-all exception handling
def process_payment(payment_id: int):
    try:
        charge_card(payment_id)
    except:  # Catches everything!
        return {"status": "failed"}
```

### 3. Logging
```python
# ✅ Good: Structured logging with context
import structlog

logger = structlog.get_logger()

@task
def process_order(order_id: int):
    logger.info("order_processing_started", order_id=order_id)
    
    try:
        order = Order.get(order_id)
        logger.info("order_retrieved", items_count=len(order.items))
        
        process_items(order)
        
        logger.info("order_processing_complete", status="success")
    except Exception as e:
        logger.error("order_processing_failed", error=str(e), exc_info=True)
        raise

# ❌ Bad: Unstructured logging
import logging
logger = logging.getLogger(__name__)

@task
def process_order(order_id):
    logger.info(f"Processing order {order_id}...")  # Hard to parse
    # ...
```

### 4. Monitoring
```python
# ✅ Good: Emit metrics for observability
from prometheus_client import Counter, Histogram

TASK_COUNTER = Counter('tasks_total', 'Total tasks', ['name', 'status'])
TASK_DURATION = Histogram('task_duration_seconds', 'Task duration', ['name'])

@task
def process_payment(payment_id):
    with TASK_DURATION.labels(name="process_payment").time():
        try:
            charge_card(payment_id)
            TASK_COUNTER.labels(name="process_payment", status="success").inc()
        except Exception as e:
            TASK_COUNTER.labels(name="process_payment", status="failure").inc()
            raise
```

### 5. Configuration Management
```python
# ✅ Good: Environment-based configuration
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_HOST: str = "localhost"
    LOG_LEVEL: str = "INFO"
    WORKER_CONCURRENCY: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings()

# ❌ Bad: Hardcoded configuration
DATABASE_URL = "postgresql://user:pass@localhost/db"
WORKER_CONCURRENCY = 5
```

### 6. Testing
```python
# ✅ Good: Comprehensive test coverage
def test_task_success():
    task = create_task(name="process_payment", args=[100])
    result = execute_task(task)
    assert result["status"] == "success"

def test_task_failure_with_retry():
    task = create_task(name="flaky_task", max_retries=3)
    with patch("external_api.call", side_effect=TimeoutError()):
        with pytest.raises(TimeoutError):
            execute_task(task)
    assert task.retry_count == 1

def test_task_idempotency():
    """Task should be safe to execute multiple times"""
    task = create_task(name="send_email", args=["user@example.com"])
    result1 = execute_task(task)
    result2 = execute_task(task)
    assert result1 == result2

# ❌ Bad: No test coverage
```

---

## FAQ

**Q: How do I scale to 1 million tasks/day?**
A: 
1. Use multiple worker instances (10-20)
2. Increase database pool size and add read replicas
3. Configure Redis for persistence and high throughput
4. Implement task prioritization to handle spikes
5. Use load balancing and horizontal scaling

**Q: What's the maximum task size?**
A: Recommended < 1MB. For larger data:
- Store data in S3/database
- Pass only reference/ID to task
- Use external data sources

**Q: How long can tasks run?**
A: Default timeout is 3600 seconds (1 hour). Configure:
```python
task = Task(name="long_task", timeout_seconds=7200)  # 2 hours
```

**Q: Can I prioritize tasks dynamically?**
A: Yes, use boost priority:
```bash
curl -X POST http://localhost:8000/api/v1/tasks/{id}/boost-priority
```

**Q: How do I handle dependencies between tasks?**
A: Use task dependencies:
```python
task1 = create_task(name="fetch_data")
task2 = create_task(name="process_data", depends_on=[task1.id])
```

**Q: What happens if a worker crashes?**
A: 
- Heartbeat timeout triggers (5 min)
- Orphaned tasks moved to failed queue
- Auto-recovery attempts restart
- Dead letter queue captures unprocessable tasks

**Q: How do I monitor in production?**
A: Use Prometheus + Grafana:
1. Scrape `/metrics` endpoint
2. Import provided dashboards
3. Set up AlertManager for alerts
4. Use OpenTelemetry for distributed tracing

**Q: Can I retry failed tasks?**
A: Yes, multiple methods:
- Automatic exponential backoff (built-in)
- Manual replay via API
- Batch retry with search filters

**Q: How do I backup my data?**
A: Backup both systems:
```bash
# PostgreSQL backup
pg_dump taskqueue > backup.sql

# Redis backup
redis-cli BGSAVE
# Or configure AOF persistence
```

---

## Support
- **Documentation**: https://docs.taskqueue.io
- **GitHub Issues**: https://github.com/taskqueue/issues
- **Community Chat**: Discord
- **Enterprise Support**: support@taskqueue.io
