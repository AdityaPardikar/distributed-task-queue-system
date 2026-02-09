"""Tests for authentication service"""

import uuid
from datetime import datetime, timedelta

import pytest
from jose import jwt

from src.services.auth_service import AuthService
from src.models import User
from src.config import get_settings

settings = get_settings()


class TestAuthService:
    """Test suite for AuthService"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)
        
        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = AuthService.hash_password(password)
        
        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """Test JWT access token creation"""
        user_id = str(uuid.uuid4())
        username = "testuser"
        role = "viewer"
        
        token = AuthService.create_access_token(user_id, username, role)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token contents
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["role"] == role
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token(self):
        """Test JWT refresh token creation"""
        user_id = str(uuid.uuid4())
        
        token = AuthService.create_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token contents
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_decode_token_valid(self):
        """Test decoding a valid token"""
        user_id = str(uuid.uuid4())
        username = "testuser"
        role = "admin"
        
        token = AuthService.create_access_token(user_id, username, role)
        payload = AuthService.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["role"] == role

    def test_decode_token_expired(self):
        """Test decoding an expired token"""
        user_id = str(uuid.uuid4())
        
        # Create token that expires immediately
        payload = {
            "sub": user_id,
            "type": "access",
            "exp": datetime.utcnow() - timedelta(seconds=1)
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        decoded = AuthService.decode_token(token)
        assert decoded is None

    def test_decode_token_invalid(self):
        """Test decoding an invalid token"""
        invalid_token = "invalid.jwt.token"
        decoded = AuthService.decode_token(invalid_token)
        assert decoded is None

    def test_authenticate_user_success(self, db_session):
        """Test successful user authentication"""
        # Create test user
        user_id = uuid.uuid4()
        password = "test_password_123"
        hashed_password = AuthService.hash_password(password)
        
        user = User(
            user_id=user_id,
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Authenticate
        authenticated_user = AuthService.authenticate_user(db_session, "testuser", password)
        
        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"
        assert authenticated_user.user_id == user_id

    def test_authenticate_user_wrong_password(self, db_session):
        """Test authentication with wrong password"""
        # Create test user
        user_id = uuid.uuid4()
        password = "test_password_123"
        hashed_password = AuthService.hash_password(password)
        
        user = User(
            user_id=user_id,
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Try to authenticate with wrong password
        authenticated_user = AuthService.authenticate_user(db_session, "testuser", "wrong_password")
        
        assert authenticated_user is None

    def test_authenticate_user_nonexistent(self, db_session):
        """Test authentication with non-existent user"""
        authenticated_user = AuthService.authenticate_user(db_session, "nonexistent", "password")
        assert authenticated_user is None

    def test_authenticate_user_inactive(self, db_session):
        """Test authentication with inactive user"""
        # Create inactive user
        user_id = uuid.uuid4()
        password = "test_password_123"
        hashed_password = AuthService.hash_password(password)
        
        user = User(
            user_id=user_id,
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Try to authenticate
        authenticated_user = AuthService.authenticate_user(db_session, "inactiveuser", password)
        
        assert authenticated_user is None

    def test_create_user_success(self, db_session):
        """Test successful user creation"""
        user = AuthService.create_user(
            db_session,
            username="newuser",
            email="new@example.com",
            password="password123",
            full_name="New User",
            role="viewer"
        )
        
        assert user is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.full_name == "New User"
        assert user.role == "viewer"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.hashed_password != "password123"

    def test_create_user_duplicate_username(self, db_session):
        """Test user creation with duplicate username"""
        # Create first user
        AuthService.create_user(
            db_session,
            username="duplicate",
            email="user1@example.com",
            password="password123"
        )
        
        # Try to create second user with same username
        with pytest.raises(Exception):
            AuthService.create_user(
                db_session,
                username="duplicate",
                email="user2@example.com",
                password="password123"
            )

    def test_has_permission_admin(self):
        """Test admin has access to all roles"""
        assert AuthService.has_permission("admin", "admin") is True
        assert AuthService.has_permission("admin", "operator") is True
        assert AuthService.has_permission("admin", "viewer") is True

    def test_has_permission_operator(self):
        """Test operator has access to operator and viewer"""
        assert AuthService.has_permission("operator", "admin") is False
        assert AuthService.has_permission("operator", "operator") is True
        assert AuthService.has_permission("operator", "viewer") is True

    def test_has_permission_viewer(self):
        """Test viewer only has access to viewer"""
        assert AuthService.has_permission("viewer", "admin") is False
        assert AuthService.has_permission("viewer", "operator") is False
        assert AuthService.has_permission("viewer", "viewer") is True

    def test_has_permission_invalid_role(self):
        """Test permission check with invalid role"""
        assert AuthService.has_permission("invalid", "admin") is False
        assert AuthService.has_permission("viewer", "invalid") is False
