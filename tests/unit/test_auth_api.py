"""Tests for authentication API endpoints"""

import uuid

import pytest

from src.models import User
from src.services.auth_service import AuthService
from src.config import get_settings


settings = get_settings()
auth_service = AuthService(settings)


class TestAuthAPI:
    """Test suite for authentication API endpoints"""

    def test_register_success(self, client):
        """Test successful user registration"""
        uname = f"newuser_{uuid.uuid4().hex[:8]}"
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": uname,
                "email": f"{uname}@example.com",
                "password": "password123",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert data["username"] == uname
        assert data["role"] == "viewer"
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client, db_session):
        """Test registration with duplicate username"""
        uname = f"dup_{uuid.uuid4().hex[:8]}"
        # Create first user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": uname,
                "email": f"{uname}_1@example.com",
                "password": "password123",
            },
        )

        # Try to register with same username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": uname,
                "email": f"{uname}_2@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 400

    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "password123",
            },
        )

        assert response.status_code == 422

    def test_login_success(self, client, db_session):
        """Test successful login"""
        password = "password123"
        hashed_password = auth_service.hash_password(password)
        uname = f"login_{uuid.uuid4().hex[:8]}"
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

        response = client.post(
            "/api/v1/auth/login",
            data={"username": uname, "password": password},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, db_session):
        """Test login with wrong password"""
        password = "password123"
        hashed_password = auth_service.hash_password(password)
        uname = f"wrongpw_{uuid.uuid4().hex[:8]}"
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

        response = client.post(
            "/api/v1/auth/login",
            data={"username": uname, "password": "wrongpassword"},
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent_user_xyz", "password": "password123"},
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, db_session):
        """Test getting current user info"""
        password = "password123"
        hashed_password = auth_service.hash_password(password)
        uname = f"meuser_{uuid.uuid4().hex[:8]}"
        user = User(
            user_id=str(uuid.uuid4()),
            username=uname,
            email=f"{uname}@example.com",
            hashed_password=hashed_password,
            role="operator",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        db_session.commit()

        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": uname, "password": password},
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == uname
        assert data["role"] == "operator"

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    def test_refresh_token_success(self, client, db_session):
        """Test token refresh"""
        password = "password123"
        hashed_password = auth_service.hash_password(password)
        uname = f"refresh_{uuid.uuid4().hex[:8]}"
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

        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": uname, "password": password},
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401

    def test_list_users_admin(self, client, db_session):
        """Test listing users as admin"""
        password = "admin123"
        hashed_password = auth_service.hash_password(password)
        uname = f"admin_{uuid.uuid4().hex[:8]}"
        admin = User(
            user_id=str(uuid.uuid4()),
            username=uname,
            email=f"{uname}@example.com",
            hashed_password=hashed_password,
            role="admin",
            is_active=True,
            is_superuser=True,
        )
        db_session.add(admin)
        db_session.commit()

        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": uname, "password": password},
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_users_non_admin(self, client, db_session):
        """Test listing users as non-admin (should fail)"""
        password = "viewer123"
        hashed_password = auth_service.hash_password(password)
        uname = f"viewer_{uuid.uuid4().hex[:8]}"
        viewer = User(
            user_id=str(uuid.uuid4()),
            username=uname,
            email=f"{uname}@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(viewer)
        db_session.commit()

        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": uname, "password": password},
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
