"""Simplified test app for debugging"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import only auth router
from src.api.routes import auth
from src.config import get_settings

settings = get_settings()

app = FastAPI(title="TaskFlow Test", version="0.1.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only auth router for testing
app.include_router(auth.router, prefix="/api/v1")

print("Test app created successfully")
