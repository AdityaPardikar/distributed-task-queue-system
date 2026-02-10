"""Authentication middleware and dependencies for FastAPI."""

from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.config.settings import Settings
from src.db.session import get_db
from src.models import User
from src.services.auth_service import AuthService

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Initialize settings and auth service
settings = Settings()
auth_service = AuthService(settings)


def get_auth_service() -> AuthService:
    """Dependency to get the auth service."""
    return auth_service


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), auth_svc: AuthService = Depends(get_auth_service)
) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = auth_svc.decode_token(token)

    # Verify token type
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    user = auth_svc.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(required_role: str):
    """Dependency factory to require a specific role.
    
    Args:
        required_role: The minimum role required (admin, operator, or viewer)
    
    Returns:
        A dependency function that checks user role
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
    """

    async def role_checker(
        current_user: User = Depends(get_current_user), auth_svc: AuthService = Depends(get_auth_service)
    ) -> User:
        if not auth_svc.has_permission(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. {required_role} role required.",
            )
        return current_user

    return role_checker


def require_admin(current_user: User = Depends(require_role("admin"))):
    """Dependency to require admin role."""
    return current_user


def require_operator(current_user: User = Depends(require_role("operator"))):
    """Dependency to require operator role (or higher)."""
    return current_user


# Optional user dependency (doesn't raise error if not authenticated)
async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    auth_svc: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    """Dependency to get the current user if authenticated, None otherwise."""
    if not token:
        return None

    try:
        payload = auth_svc.decode_token(token)
        user_id = payload.get("sub")
        if user_id:
            user = auth_svc.get_user_by_id(db, user_id)
            if user and user.is_active:
                return user
    except HTTPException:
        pass

    return None
