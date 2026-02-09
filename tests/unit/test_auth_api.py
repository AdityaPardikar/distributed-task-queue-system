"""Tests for authentication API endpoints"""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.models import User
from src.services.auth_service import AuthService
from src.db.session import get_session

client = TestClient(app)


class TestAuthAPI:
    """Test suite for authentication API endpoints"""

    def test_register_success(self, db_session):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "viewer"
        assert "user_id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, db_session):
        """Test registration with duplicate username"""
        # Create first user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "user1@example.com",
                "password": "password123"
            }
        )
        
        # Try to register with same username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "user2@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400

    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422

    def test_login_success(self, db_session):
        """Test successful login"""
        # Create test user
        password = "password123"
        hashed_password = AuthService.hash_password(password)
        user = User(
            user_id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, db_session):
        """Test login with wrong password"""
        # Create test user
        password = "password123"
        hashed_password = AuthService.hash_password(password)
        user = User(
            user_id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Try to login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401

    def test_get_current_user(self, db_session):
        """Test getting current user info"""
        # Create and login user
        password = "password123"
        hashed_password = AuthService.hash_password(password)
        user = User(
            user_id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            role="operator",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": password
            }
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "operator"

    def test_get_current_user_unauthorized(self):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_refresh_token_success(self, db_session):
        """Test token refresh"""
        # Create and login user
        password = "password123"
        hashed_password = AuthService.hash_password(password)
        user = User(
            user_id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": password
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self):
        """Test token refresh with invalid token"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == 401

    def test_list_users_admin(self, db_session):
        """Test listing users as admin"""
        # Create admin user
        password = "admin123"
        hashed_password = AuthService.hash_password(password)
        admin = User(
            user_id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            role="admin",
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        
        # Login as admin
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": password
            }
        )
        token = login_response.json()["access_token"]
        
        # List users
        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data

    def test_list_users_non_admin(self, db_session):
        """Test listing users as non-admin (should fail)"""
        # Create viewer user
        password = "viewer123"
        hashed_password = AuthService.hash_password(password)
        viewer = User(
            user_id=uuid.uuid4(),
            username="viewer",
            email="viewer@example.com",
            hashed_password=hashed_password,
            role="viewer",
            is_active=True
        )
        db_session.add(viewer)
        db_session.commit()
        
        # Login as viewer
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "viewer",
                "password": password
            }
        )
        token = login_response.json()["access_token"]
        
        # Try to list users
        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403

    def test_update_user_role_admin(self, db_session):
        """Test updating user role as admin"""
        # Create admin and target user
        admin_password = "admin123"
        admin_hashed = AuthService.hash_password(admin_password)
        admin = User(
            user_id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",
            hashed_password=admin_hashed,
            role="admin",
            is_active=True
        )
        
        target_user_id = uuid.uuid4()
        target = User(
            user_id=target_user_id,
            username="targetuser",
            email="target@example.com",
            hashed_password=AuthService.hash_password("password"),
            role="viewer",
            is_active=True
        )
        
        db_session.add(admin)
        db_session.add(target)
        db_session.commit()
        
        # Login as admin
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": admin_password
            }
        )
        token = login_response.json()["access_token"]
        
        # Update target user's role
        response = client.patch(
            f"/api/v1/auth/users/{target_user_id}/role",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "operator"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "operator"

    def test_update_user_status_admin(self, db_session):
        """Test updating user status as admin"""
        # Create admin and target user
        admin_password = "admin123"
        admin_hashed = AuthService.hash_password(admin_password)
        admin = User(
            user_id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",
            hashed_password=admin_hashed,
            role="admin",
            is_active=True
        )
        
        target_user_id = uuid.uuid4()
        target = User(
            user_id=target_user_id,
            username="targetuser",
            email="target@example.com",
            hashed_password=AuthService.hash_password("password"),
            role="viewer",
            is_active=True
        )
        
        db_session.add(admin)
        db_session.add(target)
        db_session.commit()
        
        # Login as admin
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": admin_password
            }
        )
        token = login_response.json()["access_token"]
        
        # Deactivate target user
        response = client.patch(
            f"/api/v1/auth/users/{target_user_id}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_active": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
