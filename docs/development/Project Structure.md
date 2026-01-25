taskflow/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # CI/CD pipeline
│       └── deploy.yml                # Deployment automation
│
├── src/
│   ├── api/                          # FastAPI REST API
│   │   ├── __init__.py
│   │   ├── main.py                   # API entry point
│   │   ├── routes/
│   │   │   ├── tasks.py              # Task endpoints
│   │   │   ├── workers.py            # Worker endpoints
│   │   │   ├── campaigns.py          # Campaign endpoints
│   │   │   ├── metrics.py            # Metrics endpoints
│   │   │   └── health.py             # Health checks
│   │   ├── dependencies.py           # FastAPI dependencies
│   │   ├── middleware.py             # Auth, rate limiting
│   │   └── schemas.py                # Pydantic models
│   │
│   ├── core/                         # Core task queue logic
│   │   ├── __init__.py
│   │   ├── broker.py                 # Redis broker interface
│   │   ├── coordinator.py            # Task coordinator
│   │   ├── worker.py                 # Worker node logic
│   │   ├── scheduler.py              # Scheduled task handler
│   │   ├── priority_queue.py         # Priority queue manager
│   │   └── dlq.py                    # Dead letter queue
│   │
│   ├── tasks/                        # Task definitions
│   │   ├── __init__.py
│   │   ├── base.py                   # Base task class
│   │   ├── email_tasks.py            # Email-specific tasks
│   │   ├── retry_logic.py            # Retry strategies
│   │   └── task_registry.py          # Task registration
│   │
│   ├── services/                     # Business logic services
│   │   ├── __init__.py
│   │   ├── campaign_service.py       # Campaign management
│   │   ├── email_service.py          # Email sending
│   │   ├── template_service.py       # Template rendering
│   │   └── analytics_service.py      # Analytics/reporting
│   │
│   ├── models/                       # Database models
│   │   ├── __init__.py
│   │   ├── task.py
│   │   ├── worker.py
│   │   ├── campaign.py
│   │   └── base.py                   # Base model
│   │
│   ├── db/                           # Database layer
│   │   ├── __init__.py
│   │   ├── session.py                # DB session management
│   │   ├── migrations/               # Alembic migrations
│   │   └── repositories/             # Data access layer
│   │       ├── task_repository.py
│   │       ├── worker_repository.py
│   │       └── campaign_repository.py
│   │
│   ├── cache/                        # Redis cache layer
│   │   ├── __init__.py
│   │   ├── client.py                 # Redis client
│   │   └── keys.py                   # Cache key patterns
│   │
│   ├── monitoring/                   # Observability
│   │   ├── __init__.py
│   │   ├── metrics.py                # Prometheus metrics
│   │   ├── logging.py                # Structured logging
│   │   └── tracing.py                # Distributed tracing
│   │
│   ├── config/                       # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py               # Pydantic settings
│   │   └── constants.py              # Constants
│   │
│   └── utils/                        # Utilities
│       ├── __init__.py
│       ├── validators.py
│       ├── serializers.py
│       └── helpers.py
│
├── dashboard/                        # React dashboard
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TaskList.jsx
│   │   │   ├── WorkerStatus.jsx
│   │   │   ├── CampaignDashboard.jsx
│   │   │   ├── MetricsChart.jsx
│   │   │   └── RealTimeUpdates.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Tasks.jsx
│   │   │   ├── Campaigns.jsx
│   │   │   └── Workers.jsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js
│   │   │   └── useMetrics.js
│   │   ├── api/
│   │   │   └── client.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── cli/                              # CLI tool
│   ├── __init__.py
│   ├── main.py                       # Click CLI
│   ├── commands/
│   │   ├── task.py
│   │   ├── worker.py
│   │   └── campaign.py
│   └── utils.py
│
├── tests/                            # Test suite
│   ├── unit/
│   │   ├── test_broker.py
│   │   ├── test_coordinator.py
│   │   ├── test_worker.py
│   │   └── test_tasks.py
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_task_flow.py
│   │   └── test_campaigns.py
│   ├── performance/
│   │   ├── test_load.py
│   │   └── test_concurrency.py
│   └── conftest.py
│
├── scripts/                          # Utility scripts
│   ├── setup_db.py
│   ├── seed_data.py
│   ├── benchmark.py
│   └── simulate_load.py
│
├── deployment/                       # Deployment configs
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.worker
│   │   └── Dockerfile.dashboard
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx/
│   │   └── nginx.conf
│   └── kubernetes/                   # K8s configs (optional)
│       ├── deployment.yaml
│       └── service.yaml
│
├── monitoring/                       # Monitoring configs
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       │   ├── tasks.json
│       │   ├── workers.json
│       │   └── campaigns.json
│       └── provisioning/
│
├── docs/                             # Documentation
│   ├── architecture.md
│   ├── api.md
│   ├── deployment.md
│   └── development.md
│
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── README.md
└── LICENSE