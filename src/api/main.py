"""FastAPI application setup"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware import add_request_id, request_timing_middleware
from src.api.security import SecurityHeadersMiddleware, tiered_rate_limit_middleware
from src.api.routes import alerts, analytics, auth, campaigns, dashboard, debug, health, metrics, operations, performance, resilience, search, tasks, templates, workers, workflows, advanced_workflows, chaos, websocket
from src.config import get_settings
from src.config.security import get_security_config
from src.core.event_bus import get_event_bus
from src.performance.profiler import get_profiler

settings = get_settings()
security_config = get_security_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context"""
    print(f"Starting {settings.APP_NAME} v{settings.VERSION}")

    # Register the WebSocket connection manager with the event bus
    from src.api.routes.websocket import get_connection_manager
    manager = get_connection_manager()
    manager.register_with_event_bus()

    yield

    # Cleanup
    manager.unregister_from_event_bus()
    print(f"Shutting down {settings.APP_NAME}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Production-grade distributed task queue system",
        lifespan=lifespan,
    )

    # Middleware - Order matters! (outermost runs first)
    # 1. Security headers on every response
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. Trusted-host check (skip in test)
    if settings.APP_ENV != "test":
        try:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)
        except:
            pass

    # 3. CORS — use hardened config from security module
    cors = security_config.cors
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors.allow_origins,
        allow_credentials=cors.allow_credentials,
        allow_methods=list(cors.allow_methods),
        allow_headers=list(cors.allow_headers),
        expose_headers=list(cors.expose_headers),
        max_age=cors.max_age,
    )

    # Custom middleware — request ID, timing, tiered rate limiting
    @app.middleware("http")
    async def _request_id_mw(request: Request, call_next):
        return await add_request_id(request, call_next)

    @app.middleware("http")
    async def _request_timing_mw(request: Request, call_next):
        return await request_timing_middleware(request, call_next)

    if settings.RATE_LIMIT_ENABLED:
        @app.middleware("http")
        async def _rate_limit_mw(request: Request, call_next):
            return await tiered_rate_limit_middleware(request, call_next)

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
    app.include_router(websocket.router)  # WebSocket endpoints (no prefix — /ws/*)

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
        app.include_router(operations.router, prefix="/api/v1", tags=["operations"])
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
