"""FastAPI application setup"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware import add_request_id, rate_limit_middleware, request_timing_middleware
from src.api.routes import alerts, analytics, auth, campaigns, dashboard, debug, health, metrics, performance, resilience, search, tasks, templates, workers, workflows, advanced_workflows, chaos
from src.config import get_settings
from src.performance.profiler import get_profiler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context"""
    print(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    yield
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
    # Skip TrustedHostMiddleware in test environment
    if settings.APP_ENV != "test":
        try:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)
        except:
            pass

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware - performance tracking
    @app.middleware("http")
    async def performance_tracking_middleware(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        profiler = get_profiler()
        profiler.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response

    # Include routers
    app.include_router(health.router)
    
    try:
        app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
        app.include_router(workers.router, prefix="/api/v1", tags=["workers"])
        app.include_router(campaigns.router, prefix="/api/v1", tags=["campaigns"])
        app.include_router(templates.router, prefix="/api/v1", tags=["templates"])
        app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
        app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
        app.include_router(search.router, prefix="/api/v1", tags=["search"])
        app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
        app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
        app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
        app.include_router(resilience.router, prefix="/api/v1", tags=["resilience"])
        app.include_router(debug.router, prefix="/api/v1", tags=["debug"])
        app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
        app.include_router(advanced_workflows.router, prefix="/api/v1", tags=["advanced-workflows"])
        app.include_router(chaos.router, prefix="/api/v1", tags=["chaos-engineering"])
        app.include_router(performance.router, prefix="/api/v1", tags=["performance"])
    except Exception as e:
        print(f"Warning: Could not load some routers: {e}")
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "status": "online",
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "docs": f"{settings.API_BASE_URL}/docs"
        }

    return app


app = create_app()
