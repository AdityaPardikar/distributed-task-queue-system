"""Tests for authentication service"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from src.services.auth_service import AuthService
from src.models import User
from src.config import get_settings

settings = get_settings()
auth_service = AuthService(settings)


class TestAuthService:
    """Test suite for AuthService"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """Test JWT access token creation"""
        user_id = str(uuid.uuid4())
        username = "testuser"
        role = "viewer"

        token = auth_service.create_access_token(
            data={"sub": user_id, "username": username, "role": role}
        )

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify token contents
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["role"] == role
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token(self):
        """Test JWT refresh token creation"""
        user_id = str(uuid.uuid4())

        token = auth_service.create_refresh_token(
            data={"sub": user_id}
        )

        assert token is not None
        assert isinstance(token, str)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_decode_token_valid(self):
        """Test decoding a valid token"""
        user_id = str(uuid.uuid4())
        username = "testuser"
        role = "admin"

        token = auth_service.create_access_token(
            data={"sub": user_id, "username": username, "role": role}
        )
        payload = auth_service.decode_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["role"] == role

    def test_decode_token_invalid(self):
        """Test decoding an invalid token raises HTTPException"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            auth_service.decode_token("invalid.jwt.token")
        assert exc_info.value.status_code == 401

    def test_authenticate_user_success(self, db_session):
        """Test successful user authentication"""
        password = "test_password_123"
        hashed_password = auth_service.hash_password(password)
        uname = f"authuser_{uuid.uuid4().hex[:8]}"

        user = User(
            user_id=str(uuid.uuid4()),
            username=uname,
            email=f"{uname}@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        db_session.commit()

        authenticated_user = auth_service.authenticate_user(db_session, uname, password)

        assert authenticated_user is not None
        assert authenticated_user.username == uname

    def test_authenticate_user_wrong_password(self, db_session):
        """Test authentication with wrong password"""
        password = "test_password_123"
        hashed_password = auth_service.hash_password(password)
        uname = f"wrongauth_{uuid.uuid4().hex[:8]}"

        user = User(
            user_id=str(uuid.uuid4()),
            username=uname,
            email=f"{uname}@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        db_session.commit()

        authenticated_user = auth_service.authenticate_user(db_session, uname, "wrong_password")
        assert authenticated_user is None

    def test_authenticate_user_nonexistent(self, db_session):
        """Test authentication with non-existent user"""
        authenticated_user = auth_service.authenticate_user(
            db_session, "nonexistent_user", "password123"
        )
        assert authenticated_user is None

    def test_authenticate_user_inactive(self, db_session):
        """Test authentication with inactive user"""
        password = "test_password_123"
        hashed_password = auth_service.hash_password(password)
        uname = f"inactive_{uuid.uuid4().hex[:8]}"

        user = User(
            user_id=str(uuid.uuid4()),
            username=uname,
            email=f"{uname}@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=False,
            is_superuser=False,
        )
        db_session.add(user)
        db_session.commit()

        authenticated_user = auth_service.authenticate_user(db_session, uname, password)
        assert authenticated_user is None

    def test_create_user(self, db_session):
        """Test creating a new user via service"""
        uname = f"create_{uuid.uuid4().hex[:8]}"
        user = auth_service.create_user(
            db=db_session,
            username=uname,
            email=f"{uname}@example.com",
            password="password123",
            full_name="Created User",
            role="viewer",
        )

        assert user is not None
        assert user.username == uname
        assert user.role == "viewer"
        assert user.is_active is True

    def test_create_user_duplicate_username(self, db_session):
        """Test creating a user with duplicate username"""
        from fastapi import HTTPException

        uname = f"dupuser_{uuid.uuid4().hex[:8]}"
        auth_service.create_user(
            db=db_session,
            username=uname,
            email=f"{uname}_1@example.com",
            password="password123",
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_service.create_user(
                db=db_session,
                username=uname,
                email=f"{uname}_2@example.com",
                password="password123",
            )
        assert exc_info.value.status_code == 400

    def test_has_permission_admin(self):
        """Test admin has all permissions"""
        user = User(
            user_id=str(uuid.uuid4()),
            username="admin",
            email="admin@test.com",
            hashed_password="hash",
            role="admin",
            is_active=True,
            is_superuser=True,
        )

        assert auth_service.has_permission(user, "admin") is True
        assert auth_service.has_permission(user, "operator") is True
        assert auth_service.has_permission(user, "viewer") is True

    def test_has_permission_viewer(self):
        """Test viewer has limited permissions"""
        user = User(
            user_id=str(uuid.uuid4()),
            username="viewer",
            email="viewer@test.com",
            hashed_password="hash",
            role="viewer",
            is_active=True,
            is_superuser=False,
        )

        assert auth_service.has_permission(user, "viewer") is True
        assert auth_service.has_permission(user, "operator") is False
        assert auth_service.has_permission(user, "admin") is False
