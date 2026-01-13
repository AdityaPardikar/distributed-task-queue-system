"""API middleware"""

import uuid
from time import time
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from src.cache.client import get_redis_client
from src.config import get_settings

settings = get_settings()
redis_client = get_redis_client()


async def add_request_id(request: Request, call_next: Callable):
    """Add request ID to all requests"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def rate_limit_middleware(request: Request, call_next: Callable):
    """Rate limit middleware"""
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)

    # Get user identifier
    user_id = request.headers.get("X-User-ID", request.client.host if request.client else "unknown")

    # Check rate limit
    key = f"rate_limit:api:{user_id}"
    current = redis_client.get(key)

    if current is None:
        redis_client.set(key, 1, ttl=60)
    else:
        current_count = int(current)
        if current_count >= settings.RATE_LIMIT_REQUESTS_PER_MINUTE:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        redis_client.incr(key)

    response = await call_next(request)
    return response
