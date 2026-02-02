"""FastAPI application setup"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware import add_request_id, rate_limit_middleware, request_timing_middleware
from src.api.routes import alerts, analytics, auth, campaigns, dashboard, debug, health, metrics, resilience, search, tasks, templates, workers, workflows
from src.config import get_settings

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

    # Custom middleware - skip for now
    # app.middleware("http")(add_request_id)
    # app.middleware("http")(rate_limit_middleware)
    # app.middleware("http")(request_timing_middleware)

    # Include routers
    try:
        app.include_router(health.router)
        app.include_router(auth.router, prefix="/api/v1")
    except Exception as e:
        print(f"Warning: Could not load auth routers: {e}")

    return app


app = create_app()
