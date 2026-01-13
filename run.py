"""Main entry point for FastAPI application"""

import uvicorn

from src.config import get_settings

settings = get_settings()


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )
