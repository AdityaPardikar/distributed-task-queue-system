DETAILED COMPONENT ARCHITECTURE

Component 1: API Gateway (FastAPI)
MAIN COMPONENT: FastAPI Application

INCOMING REQUESTS (Top):
- HTTP/HTTPS requests from clients
- WebSocket connections for real-time updates

MIDDLEWARE STACK (Top to Bottom):
1. CORS Middleware
   - Allow origins: dashboard domain
   - Allow methods: GET, POST, PUT, DELETE
   - Allow credentials: true

2. Request ID Middleware
   - Generate unique request_id
   - Add to headers and logs

3. Authentication Middleware
   - Verify JWT token
   - Extract user_id
   - Check token expiration

4. Rate Limiting Middleware
   - Redis-based sliding window
   - 100 requests/minute per user
   - 1000 requests/minute per IP
   - Return 429 on limit exceeded

5. Request Validator
   - Pydantic schema validation
   - Type checking
   - Return 422 on validation error

6. Logging Middleware
   - Log request method, path, duration
   - JSON structured logs
   - Include request_id, user_id

ROUTE HANDLERS (Center):

Group: Task Routes (/api/v1/tasks)
- POST /tasks → create_task()
- GET /tasks → list_tasks()
- GET /tasks/{task_id} → get_task()
- DELETE /tasks/{task_id} → cancel_task()
- POST /tasks/{task_id}/retry → retry_task()

Group: Worker Routes (/api/v1/workers)
- GET /workers → list_workers()
- GET /workers/{worker_id} → get_worker()
- POST /workers/{worker_id}/pause → pause_worker()

Group: Campaign Routes (/api/v1/campaigns)
- POST /campaigns → create_campaign()
- GET /campaigns → list_campaigns()
- GET /campaigns/{campaign_id} → get_campaign()
- POST /campaigns/{campaign_id}/start → start_campaign()
- POST /campaigns/{campaign_id}/pause → pause_campaign()

Group: Metrics Routes (/api/v1/metrics)
- GET /metrics → prometheus_metrics()
- GET /stats → system_stats()

Group: Health Routes
- GET /health → health_check()
- GET /ready → readiness_check()

DEPENDENCIES (Bottom):
- TaskRepository → PostgreSQL
- WorkerRepository → PostgreSQL
- CampaignRepository → PostgreSQL
- RedisClient → Redis
- CoordinatorClient → Task Coordinator (HTTP)

OUTPUT:
- JSON responses
- HTTP status codes
- WebSocket events

Component 2: Task Coordinator
Create a component diagram for Task Coordinator:

MAIN COMPONENT: Task Coordinator Service (Python daemon)

INPUTS:
- New tasks from API Gateway
- Task status updates from workers
- Scheduled task triggers
- Worker heartbeats

INTERNAL COMPONENTS:

1. Priority Queue Manager
   - Maintains 4 priority levels: CRITICAL, HIGH, MEDIUM, LOW
   - Uses Redis Sorted Sets
   - Score = (priority * 1000000) - timestamp
   - Operations:
     * add_task(task_id, priority)
     * get_next_task() → task_id
     * remove_task(task_id)

2. Scheduler Service
   - Poll scheduled tasks every 5 seconds
   - Query: SELECT * FROM tasks WHERE scheduled_at <= NOW() AND status = 'SCHEDULED'
   - Move to pending queue
   - Support cron expressions for recurring tasks
   - Operations:
     * schedule_task(task_id, schedule_at)
     * check_due_tasks()
     * trigger_task(task_id)

3. Dependency Graph Manager
   - Store parent-child relationships
   - Graph structure: adjacency list in PostgreSQL
   - Check completion: ON task_complete → trigger children
   - Circular dependency detection: DFS algorithm
   - Operations:
     * add_dependency(parent_id, child_id)
     * get_children(task_id)
     * check_circular(task_id)
     * trigger_children(task_id)

4. Dead Letter Queue Handler
   - Move failed tasks after max retries
   - Store failure reason, stack trace
   - Retention: 30 days
   - Operations:
     * move_to_dlq(task_id, reason)
     * get_dlq_items()
     * requeue_from_dlq(task_id)

5. Worker Health Monitor
   - Track last heartbeat timestamp per worker
   - Poll every 10 seconds
   - Mark dead if no heartbeat for 30 seconds
   - Reassign running tasks from dead workers
   - Operations:
     * record_heartbeat(worker_id)
     * check_dead_workers()
     * reassign_tasks(worker_id)

CONNECTIONS:
- Redis: Read/write task queues, worker registry
- PostgreSQL: Read/write task metadata, worker status
- Workers: Receive heartbeats, send kill signals

OUTPUTS:
- Task assignments to workers
- Worker health status
- System metrics

Component 3: Worker Node
Create a component diagram for Worker Node:

MAIN COMPONENT: Worker Process (Python multiprocessing)

CONFIGURATION:
- Worker ID: UUID
- Capacity: 5 concurrent tasks
- Timeout: 300 seconds default
- Retry delays: [1, 2, 4, 8, 16] seconds

INTERNAL COMPONENTS:

1. Task Poller (Thread 1)
   - Infinite loop
   - BLPOP from Redis queue (blocking, 5s timeout)
   - Check capacity before accepting
   - Algorithm:
   while running:
     if current_load < capacity:
         task = redis.blpop('task_queue', timeout=5)
         if task:
             executor.submit(task)
     time.sleep(0.1)
     2. Task Executor (Thread Pool)
   - ThreadPoolExecutor with 5 workers
   - Execute task function with args
   - Handle exceptions
   - Enforce timeout with signals
   - Flow:
   1. Update status: PENDING → RUNNING
 2. Load task function from registry
 3. Execute: result = func(**task_args)
 4. Handle success: store result, status = COMPLETED
 5. Handle failure: log error, status = FAILED
 6. Handle timeout: send SIGTERM, status = TIMEOUT
3. Heartbeat Sender (Thread 2)
   - Send heartbeat every 10 seconds
   - Include: worker_id, hostname, current_load, status
   - Redis: HSET worker:{worker_id} last_heartbeat timestamp
   - Also update PostgreSQL workers table

4. Result Publisher
   - Store results in PostgreSQL
   - Publish completion event to Redis Pub/Sub
   - Update task metrics in Prometheus

5. Retry Handler
   - On task failure, check retry_count < max_retries
   - Calculate delay: 2^retry_count seconds
   - Push back to queue with delay
   - Increment retry_count

CONNECTIONS:
- Redis: Poll tasks, publish heartbeat
- PostgreSQL: Update task status, store results
- Email Service: Call for email tasks
- Metrics: Export to Prometheus

OUTPUTS:
- Task results
- Task logs
- Worker metrics
- Heartbeat signals

Component 4: Database Schema Details
Create a detailed database schema diagram:

DATABASE: PostgreSQL 15

TABLE: tasks
- task_id: UUID PRIMARY KEY
- task_name: VARCHAR(255) NOT NULL
- task_args: JSONB
- task_kwargs: JSONB
- priority: INTEGER DEFAULT 5 (1-10, higher = more important)
- status: VARCHAR(50) [PENDING, SCHEDULED, RUNNING, COMPLETED, FAILED, CANCELLED, TIMEOUT]
- retry_count: INTEGER DEFAULT 0
- max_retries: INTEGER DEFAULT 5
- timeout_seconds: INTEGER DEFAULT 300
- parent_task_id: UUID FOREIGN KEY → tasks(task_id)
- campaign_id: UUID FOREIGN KEY → campaigns(campaign_id)
- created_at: TIMESTAMP DEFAULT NOW()
- scheduled_at: TIMESTAMP
- started_at: TIMESTAMP
- completed_at: TIMESTAMP
- worker_id: UUID FOREIGN KEY → workers(worker_id)
- created_by: UUID (user_id)

INDEXES:
- idx_status_priority ON tasks(status, priority DESC)
- idx_scheduled_at ON tasks(scheduled_at) WHERE status = 'SCHEDULED'
- idx_campaign_id ON tasks(campaign_id)
- idx_created_at ON tasks(created_at DESC)

TABLE: task_results
- result_id: UUID PRIMARY KEY
- task_id: UUID FOREIGN KEY → tasks(task_id) UNIQUE
- result_data: JSONB
- error_message: TEXT
- stack_trace: TEXT
- created_at: TIMESTAMP DEFAULT NOW()

TABLE: task_logs
- log_id: UUID PRIMARY KEY
- task_id: UUID FOREIGN KEY → tasks(task_id)
- level: VARCHAR(20) [DEBUG, INFO, WARNING, ERROR]
- message: TEXT NOT NULL
- metadata: JSONB
- created_at: TIMESTAMP DEFAULT NOW()

INDEX: idx_task_logs_task_id ON task_logs(task_id, created_at DESC)

TABLE: workers
- worker_id: UUID PRIMARY KEY
- hostname: VARCHAR(255)
- status: VARCHAR(50) [ACTIVE, IDLE, BUSY, DEAD]
- capacity: INTEGER DEFAULT 5
- current_load: INTEGER DEFAULT 0
- last_heartbeat: TIMESTAMP
- registered_at: TIMESTAMP DEFAULT NOW()
- metadata: JSONB (version, platform, etc.)

INDEX: idx_workers_heartbeat ON workers(last_heartbeat DESC)

TABLE: task_executions
- execution_id: UUID PRIMARY KEY
- task_id: UUID FOREIGN KEY → tasks(task_id)
- worker_id: UUID FOREIGN KEY → workers(worker_id)
- attempt_number: INTEGER
- started_at: TIMESTAMP DEFAULT NOW()
- completed_at: TIMESTAMP
- duration_seconds: DECIMAL(10,3)
- status: VARCHAR(50)
- error_message: TEXT

TABLE: campaigns
- campaign_id: UUID PRIMARY KEY
- name: VARCHAR(255) NOT NULL
- status: VARCHAR(50) [DRAFT, SCHEDULED, RUNNING, PAUSED, COMPLETED, FAILED]
- template_subject: VARCHAR(255)
- template_body: TEXT
- template_variables: JSONB
- total_recipients: INTEGER DEFAULT 0
- sent_count: INTEGER DEFAULT 0
- failed_count: INTEGER DEFAULT 0
- created_at: TIMESTAMP DEFAULT NOW()
- scheduled_at: TIMESTAMP
- started_at: TIMESTAMP
- completed_at: TIMESTAMP
- created_by: UUID (user_id)
- rate_limit_per_minute: INTEGER DEFAULT 100

TABLE: email_recipients
- recipient_id: UUID PRIMARY KEY
- campaign_id: UUID FOREIGN KEY → campaigns(campaign_id)
- email: VARCHAR(255) NOT NULL
- status: VARCHAR(50) [PENDING, SENT, FAILED, BOUNCED, UNSUBSCRIBED]
- personalization: JSONB (name, custom fields)
- sent_at: TIMESTAMP
- task_id: UUID FOREIGN KEY → tasks(task_id)
- error_message: TEXT
- bounce_reason: TEXT

INDEX: idx_email_campaign_status ON email_recipients(campaign_id, status)

TABLE: dead_letter_queue
- dlq_id: UUID PRIMARY KEY
- task_id: UUID FOREIGN KEY → tasks(task_id)
- task_data: JSONB (complete task info)
- failure_reason: TEXT NOT NULL
- total_attempts: INTEGER
- moved_at: TIMESTAMP DEFAULT NOW()
- requeued_at: TIMESTAMP

RETENTION POLICY: DELETE WHERE moved_at < NOW() - INTERVAL '30 days'

RELATIONSHIPS:
- tasks.parent_task_id → tasks.task_id (self-referencing)
- tasks.campaign_id → campaigns.campaign_id (one-to-many)
- tasks.worker_id → workers.worker_id (many-to-one)
- task_results.task_id → tasks.task_id (one-to-one)
- task_logs.task_id → tasks.task_id (one-to-many)
- task_executions.task_id → tasks.task_id (one-to-many)
- task_executions.worker_id → workers.worker_id (many-to-one)
- email_recipients.campaign_id → campaigns.campaign_id (one-to-many)
- email_recipients.task_id → tasks.task_id (one-to-one)
- dead_letter_queue.task_id → tasks.task_id (one-to-one)

Component 5: Redis Data Structures
Create a diagram showing Redis data structures:

REDIS DATABASE (DB 0)

KEY PATTERN: task:queue:{priority}
TYPE: List
PURPOSE: Store task IDs by priority
OPERATIONS:
- LPUSH task:queue:high {task_id}
- BRPOP task:queue:high 5
VALUES: ["task-uuid-1", "task-uuid-2", ...]

KEY PATTERN: task:scheduled
TYPE: Sorted Set
PURPOSE: Store scheduled tasks with timestamp as score
OPERATIONS:
- ZADD task:scheduled {timestamp} {task_id}
- ZRANGEBYSCORE task:scheduled 0 {now}
MEMBERS: {"task-uuid-1" → score: 1705234800}

KEY PATTERN: task:meta:{task_id}
TYPE: Hash
PURPOSE: Store task metadata for quick access
FIELDS:
- status: "RUNNING"
- worker_id: "worker-uuid-1"
- started_at: "2025-01-13T10:30:00Z"
- retry_count: "2"
OPERATIONS:
- HSET task:meta:{task_id} status "RUNNING"
- HGET task:meta:{task_id} status

KEY PATTERN: worker:{worker_id}
TYPE: Hash
PURPOSE: Store worker information
FIELDS:
- hostname: "worker-node-1"
- status: "BUSY"
- current_load: "3"
- capacity: "5"
- last_heartbeat: "1705234856"
TTL: 60 seconds (auto-expire if no heartbeat)

KEY PATTERN: worker:registry
TYPE: Set
PURPOSE: Active worker IDs
OPERATIONS:
- SADD worker:registry {worker_id}
- SREM worker:registry {worker_id}
- SMEMBERS worker:registry

KEY PATTERN: rate_limit:{resource}:{identifier}
TYPE: String
PURPOSE: Rate limiting counters
EXAMPLE: rate_limit:api:user:123
VALUE: "45" (request count)
TTL: 60 seconds
OPERATIONS:
- INCR rate_limit:api:user:123
- EXPIRE rate_limit:api:user:123 60

KEY PATTERN: campaign:{campaign_id}:progress
TYPE: Hash
PURPOSE: Track campaign progress
FIELDS:
- total: "10000"
- sent: "4523"
- failed: "12"
- pending: "5465"

KEY PATTERN: task:dependencies:{task_id}
TYPE: Set
PURPOSE: Store child task IDs
OPERATIONS:
- SADD task:dependencies:{parent_id} {child_id}
- SMEMBERS task:dependencies:{parent_id}

KEY PATTERN: task:completed
TYPE: Stream
PURPOSE: Event stream for completed tasks
OPERATIONS:
- XADD task:completed * task_id {id} status COMPLETED
- XREAD BLOCK 0 STREAMS task:completed $

MEMORY MANAGEMENT:
- Eviction policy: allkeys-lru
- Max memory: 2GB
- Persistence: RDB snapshots every 5 minutes

Component 6: Data Flow Diagrams
Create sequence diagrams for these flows:

FLOW 1: Task Submission & Execution
Actor: Client
Participants: API Gateway, PostgreSQL, Redis, Task Coordinator, Worker, Email Service

1. Client → API Gateway: POST /tasks
   Body: {task_name: "send_email", args: {...}, priority: "HIGH"}

2. API Gateway → PostgreSQL: INSERT INTO tasks
   Returns: task_id

3. API Gateway → Redis: LPUSH task:queue:high {task_id}

4. API Gateway → Client: 201 Created
   Body: {task_id: "...", status: "PENDING"}

5. Worker → Redis: BRPOP task:queue:high (blocking)
   Returns: task_id

6. Worker → PostgreSQL: UPDATE tasks SET status='RUNNING', worker_id='{worker_id}'

7. Worker → Email Service: send_email(args)

8. Email Service → SMTP Server: Send email
   Returns: success/failure

9. Worker → PostgreSQL: UPDATE tasks SET status='COMPLETED', completed_at=NOW()

10. Worker → PostgreSQL: INSERT INTO task_results (result_data)

11. Worker → Redis: PUBLISH task:completed {task_id}

12. API Gateway (WebSocket) → Client: Task completed notification

FLOW 2: Worker Crash Recovery
Participants: Worker 1, Worker 2, Task Coordinator, PostgreSQL, Redis

1. Worker 1 → Redis: BRPOP task:queue (get task-123)

2. Worker 1 → PostgreSQL: UPDATE tasks SET status='RUNNING' WHERE task_id='task-123'

3. Worker 1: [CRASHES] (no heartbeat sent)

4. Task Coordinator (polling every 10s) → PostgreSQL: 
   SELECT * FROM workers WHERE last_heartbeat < NOW() - INTERVAL '30 seconds'
   Returns: [Worker 1]

5. Task Coordinator → PostgreSQL: UPDATE workers SET status='DEAD' WHERE worker_id='worker-1'

6. Task Coordinator → PostgreSQL:
   SELECT task_id FROM tasks WHERE worker_id='worker-1' AND status='RUNNING'
   Returns: [task-123]

7. Task Coordinator → PostgreSQL: 
   UPDATE tasks SET status='PENDING', worker_id=NULL WHERE task_id='task-123'

8. Task Coordinator → Redis: LPUSH task:queue:high 'task-123'

9. Worker 2 → Redis: BRPOP task:queue:high
   Returns: task-123

10. Worker 2 → PostgreSQL: UPDATE tasks SET status='RUNNING', worker_id='worker-2'

11. Worker 2: Execute task successfully

12. Worker 2 → PostgreSQL: UPDATE tasks SET status='COMPLETED'

FLOW 3: Campaign Execution
Actor: User
Participants: Dashboard, API Gateway, PostgreSQL, Task Coordinator, Workers, SMTP

1. User → Dashboard: Create campaign form
   - Name: "Black Friday Sale"
   - Upload CSV: 10,000 recipients
   - Template: "Hello {{name}}, check our deals!"

2. Dashboard → API Gateway: POST /campaigns
   Body: {name: "...", recipients: [...]}

3. API Gateway → PostgreSQL: 
   INSERT INTO campaigns
   BULK INSERT INTO email_recipients (10,000 rows)
   Returns: campaign_id

4. User → Dashboard: Click "Start Campaign"

5. Dashboard → API Gateway: POST /campaigns/{id}/start

6. API Gateway → Task Coordinator: create_campaign_tasks(campaign_id)

7. Task Coordinator → PostgreSQL: 
   SELECT email, personalization FROM email_recipients WHERE campaign_id='{id}'

8. Task Coordinator (loop 10,000 times):
   - Create task for each recipient
   - INSERT INTO tasks (task_name='send_email', args={...}, campaign_id)
   - LPUSH to Redis queue

9. Workers (5 workers in parallel) → Redis: BRPOP tasks
   Each worker processes ~2000 tasks

10. Worker → Email Service → SMTP: Send email

11. Worker → PostgreSQL: 
    UPDATE email_recipients SET status='SENT', sent_at=NOW()
    UPDATE campaigns SET sent_count = sent_count + 1

12. Dashboard (WebSocket) → User: Live progress updates
    "4,523 / 10,000 sent (45.23%)"

13. All tasks complete → Task Coordinator → PostgreSQL:
    UPDATE campaigns SET status='COMPLETED', completed_at=NOW()

14. Dashboard → User: "Campaign completed! 9,988 sent, 12 failed"

📊 3. TECHNOLOGY STACK DETAILS

LAYER 1: FRONTEND
├── React 18.2.0
│   ├── React Router 6.x (routing)
│   ├── TanStack Query (data fetching)
│   └── Zustand (state management)
├── TailwindCSS 3.x (styling)
├── Recharts (charts/graphs)
├── Socket.io-client (WebSocket)
└── Axios (HTTP client)

LAYER 2: API & BACKEND
├── FastAPI 0.104.0
│   ├── Uvicorn (ASGI server)
│   ├── Pydantic 2.x (validation)
│   └── python-multipart (file uploads)
├── Python 3.11
└── Poetry (dependency management)

LAYER 3: CORE SERVICES
├── Task Queue Engine (custom Python)
├── Worker Pool (multiprocessing)
├── Scheduler (APScheduler)
└── Email Service (smtplib + Jinja2)

LAYER 4: DATABASES
├── PostgreSQL 15
│   ├── psycopg2 (driver)
│   ├── SQLAlchemy 2.0 (ORM)
│   └── Alembic (migrations)
└── Redis 7.0
    ├── redis-py (client)
    └── redis-streams (queue)

LAYER 5: OBSERVABILITY
├── Prometheus 2.45
│   └── prometheus-client (Python exporter)
├── Grafana 10.0
├── Structlog (logging)
└── OpenTelemetry (tracing - optional)

LAYER 6: INFRASTRUCTURE
├── Docker 24.0
│   └── Docker Compose 2.x
├── Nginx 1.25 (reverse proxy)
├── Let's Encrypt (SSL)
└── Linux (Ubuntu 22.04)

LAYER 7: DEVELOPMENT
├── pytest (testing)
├── locust (load testing)
├── black (formatting)
├── ruff (linting)
├── mypy (type checking)
└── pre-commit hooks

EXTERNAL SERVICES
├── SMTP Providers
│   ├── Gmail SMTP
│   ├── SendGrid
│   └── AWS SES
└── Cloud Hosting
    ├── AWS EC2
    ├── DigitalOcean
    └── Hetzner

🔄 4. DEPLOYMENT ARCHITECTURE
Create a deployment architecture diagram:

PRODUCTION ENVIRONMENT

CLOUD PROVIDER: AWS / DigitalOcean

├── LOAD BALANCER (Nginx)
│   ├── Port 443 (HTTPS)
│   ├── SSL Certificate (Let's Encrypt)
│   └── Routes:
│       ├── / → Dashboard (port 3000)
│       ├── /api → API Gateway (port 8000)
│       └── /metrics → Prometheus (port 9090)
│
├── APPLICATION TIER
│   ├── API Gateway Container
│   │   ├── Image: taskflow-api:latest
│   │   ├── Replicas: 2
│   │   ├── Resources: 1 CPU, 2GB RAM
│   │   └── Health: /health endpoint
│   │
│   ├── Worker Node Containers
│   │   ├── Image: taskflow-worker:latest
│   │   ├── Replicas: 5
│   │   ├── Resources: 2 CPU, 4GB RAM each
│   │   └── Auto-restart: always
│   │
│   ├── Task Coordinator Container
│   │   ├── Image: taskflow-coordinator:latest
│   │   ├── Replicas: 1
│   │   ├── Resources: 1 CPU, 2GB RAM
│   │   └── Singleton: true
│   │
│   └── Dashboard Container
│       ├── Image: taskflow-dashboard:latest
│       ├── Replicas: 1
│       ├── Resources: 0.5 CPU, 512MB RAM
│       └── Static files: Nginx
│
├── DATA TIER
│   ├── PostgreSQL
│   │   ├── Managed DB (AWS RDS / DO Managed)
│   │   ├── Instance: db.t3.medium
│   │   ├── Storage: 100GB SSD
│   │   ├── Backups: Daily automated
│   │   └── Replication: Multi-AZ
│   │
│   └── Redis
│       ├── Managed Redis (AWS ElastiCache / DO Managed)
│       ├── Instance: cache.t3.medium
│       ├── Memory: 4GB
│       └── Persistence: RDB + AOF
│
├── MONITORING TIER
│   ├── Prometheus Container
│   │   ├── Port: 9090
│   │   ├── Storage: 20GB volume
│   │   └── Retention: 15 days
│   │
│   └── Grafana Container
│       ├── Port: 3001
│       ├── Dashboards: Pre-configured
│       └── Alerts: Email notifications
│
└── NETWORK
    ├── VPC: 10.0.0.0/16
    ├── Public Subnet: 10.0.1.0/24
    ├── Private Subnet: 10.0.2.0/24
    ├── Security Groups:
    │   ├── ALB: 80, 443 from 0.0.0.0/0
    │   ├── App: 8000, 3000 from ALB only
    │   ├── DB: 5432 from App only
    │   └── Redis: 6379 from App only
    └── NAT Gateway: For outbound SMTP

COST ESTIMATE: $40-60/month