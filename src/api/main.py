"""FastAPI application setup"""

import logging
import time
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
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

logger = logging.getLogger(__name__)

settings = get_settings()
security_config = get_security_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context"""
    logger.info("Starting %s v%s", settings.APP_NAME, settings.VERSION)

    # Register the WebSocket connection manager with the event bus
    from src.api.routes.websocket import get_connection_manager
    manager = get_connection_manager()
    manager.register_with_event_bus()

    yield

    # Cleanup
    manager.unregister_from_event_bus()
    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Production-grade distributed task queue system",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------ #
    # Global exception handlers — consistent JSON error envelope          #
    # ------------------------------------------------------------------ #
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "detail": exc.detail,
                "status_code": exc.status_code,
            },
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "detail": "Validation error",
                "errors": exc.errors(),
                "status_code": 422,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "detail": "Internal server error",
                "status_code": 500,
            },
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

    _routers = [
        (tasks.router,             "/api/v1", ["tasks"]),
        (workers.router,           "/api/v1", ["workers"]),
        (campaigns.router,         "/api/v1", ["campaigns"]),
        (templates.router,         "/api/v1", ["templates"]),
        (analytics.router,         "/api/v1", ["analytics"]),
        (dashboard.router,         "/api/v1", ["dashboard"]),
        (search.router,            "/api/v1", ["search"]),
        (workflows.router,         "/api/v1", ["workflows"]),
        (alerts.router,            "/api/v1", ["alerts"]),
        (metrics.router,           "/api/v1", ["metrics"]),
        (resilience.router,        "/api/v1", ["resilience"]),
        (debug.router,             "/api/v1", ["debug"]),
        (auth.router,              "/api/v1", ["auth"]),
        (advanced_workflows.router,"/api/v1", ["advanced-workflows"]),
        (chaos.router,             "/api/v1", ["chaos-engineering"]),
        (performance.router,       "/api/v1", ["performance"]),
        (operations.router,        "/api/v1", ["operations"]),
    ]
    for router, prefix, tags in _routers:
        try:
            app.include_router(router, prefix=prefix, tags=tags)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load router %s: %s", tags, exc, exc_info=True)
    
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
