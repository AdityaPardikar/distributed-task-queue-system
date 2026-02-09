"""Authentication endpoints"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.api.middleware import get_auth_service, get_current_user, require_admin
from src.db.session import get_db
from src.models import User
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic schemas
class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""

    username: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema."""

    user_id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation schema."""

    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "viewer"


class UserLogin(BaseModel):
    """User login schema."""

    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


# Auth endpoints


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, db: Session = Depends(get_db), auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    try:
        user = auth_service.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role,
        )
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login and receive access and refresh tokens."""
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    auth_service.update_last_login(db, user.user_id)

    # Create tokens
    access_token = auth_service.create_access_token(data={"sub": user.user_id, "username": user.username, "role": user.role})
    refresh_token = auth_service.create_refresh_token(data={"sub": user.user_id})

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    try:
        payload = auth_service.decode_token(refresh_data.refresh_token)

        # Verify token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user = auth_service.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Create new tokens
        access_token = auth_service.create_access_token(
            data={"sub": user.user_id, "username": user.username, "role": user.role}
        )
        refresh_token = auth_service.create_refresh_token(data={"sub": user.user_id})

        return Token(access_token=access_token, refresh_token=refresh_token)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout the current user.
    
    Note: JWT tokens cannot be invalidated server-side without additional infrastructure.
    Client should discard the tokens on logout.
    """
    return {"message": "Successfully logged out. Please discard your tokens."}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """List all users (admin only)."""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get a specific user by ID (admin only)."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a user's role (admin only)."""
    if role not in ["admin", "operator", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be admin, operator, or viewer",
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = role
    user.is_superuser = role == "admin"
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate or deactivate a user (admin only)."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = is_active
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)
