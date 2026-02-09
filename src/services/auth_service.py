"""Authentication service for user management and JWT token handling."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config.settings import Settings
from src.models import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication and authorization."""

    def __init__(self, settings: Settings):
        """Initialize the auth service with settings."""
        self.settings = settings
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_hours = settings.JWT_EXPIRATION_HOURS
        self.refresh_token_expire_days = settings.JWT_REFRESH_EXPIRATION_DAYS

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=self.access_token_expire_hours)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def create_user(
        self, db: Session, username: str, email: str, password: str, full_name: Optional[str] = None, role: str = "viewer"
    ) -> User:
        """Create a new user."""
        # Check if user already exists
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Validate role
        if role not in ["admin", "operator", "viewer"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be admin, operator, or viewer",
            )

        # Create user
        hashed_password = self.hash_password(password)
        user = User(
            user_id=str(uuid4()),
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=True,
            is_superuser=(role == "admin"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get a user by username."""
        return db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get a user by email."""
        return db.query(User).filter(User.email == email).first()

    def update_last_login(self, db: Session, user_id: str) -> None:
        """Update the last login timestamp for a user."""
        user = self.get_user_by_id(db, user_id)
        if user:
            user.last_login = datetime.now(timezone.utc)
            db.commit()

    def has_permission(self, user: User, required_role: str) -> bool:
        """Check if a user has the required role permission.
        
        Role hierarchy: admin > operator > viewer
        """
        role_hierarchy = {"admin": 3, "operator": 2, "viewer": 1}
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        return user_level >= required_level
