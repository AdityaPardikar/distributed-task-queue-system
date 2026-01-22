"""FastAPI application setup"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware import add_request_id, rate_limit_middleware, request_timing_middleware
from src.api.routes import alerts, analytics, campaigns, dashboard, debug, health, metrics, search, tasks, workers, workflows
from src.config import get_settings
from src.monitoring.metrics import prometheus_response
from src.observability.logging_config import configure_logging
from src.observability.tracing import configure_tracing

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context"""
    # Startup
    configure_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    if settings.TRACING_ENABLED:
        configure_tracing(service_name=settings.APP_NAME, endpoint=settings.TRACING_ENDPOINT)
    print(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Production-grade distributed task queue system",
        lifespan=lifespan,
    )

    # Middleware - Order matters!
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    app.middleware("http")(add_request_id)
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(request_timing_middleware)

    # Include routers
    app.include_router(health.router)
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(workers.router, prefix="/api/v1")
    app.include_router(campaigns.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")
    app.include_router(workflows.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(alerts.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")

    if settings.METRICS_ENABLED:
        # Expose Prometheus scrape endpoint at /metrics
        app.add_api_route("/metrics", prometheus_response, methods=["GET"], include_in_schema=False)

    # Register routers
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(workers.router, prefix="/api/v1")
    app.include_router(workflows.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(alerts.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(debug.router, prefix="/api/v1")
    app.include_router(campaigns.router, prefix="/api/v1")
    app.include_router(health.router, prefix="/api/v1")

    return app


app = create_app()
