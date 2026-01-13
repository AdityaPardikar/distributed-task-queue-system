"""FastAPI application setup"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware import add_request_id, rate_limit_middleware
from src.api.routes import campaigns, health, metrics, tasks, workers
from src.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context"""
    # Startup
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

    # Include routers
    app.include_router(health.router)
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(workers.router, prefix="/api/v1")
    app.include_router(campaigns.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "status": "running",
        }

    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
