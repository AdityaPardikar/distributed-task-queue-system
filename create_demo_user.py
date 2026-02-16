#!/usr/bin/env python
"""Create demo admin user for testing and development."""

import sys
from uuid import uuid4

import bcrypt
from sqlalchemy.orm import Session

from src.config import get_settings
from src.db.session import get_db
from src.models import User

# Demo credentials
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "admin123"
DEMO_EMAIL = "admin@example.com"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Convert to bytes and hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_demo_user():
    """Create or update demo admin user."""
    settings = get_settings()
    
    # Get database session
    db: Session = next(get_db())
    
    try:
        # Check if user exists
        user = db.query(User).filter(User.username == DEMO_USERNAME).first()
        
        hashed_password = hash_password(DEMO_PASSWORD)
        
        if user:
            print(f"User '{DEMO_USERNAME}' already exists. Updating password...")
            user.hashed_password = hashed_password
            user.role = "admin"
            user.is_active = True
            user.is_superuser = True
            db.commit()
            print(f"✅ User '{DEMO_USERNAME}' updated successfully!")
        else:
            print(f"Creating new user '{DEMO_USERNAME}'...")
            new_user = User(
                user_id=str(uuid4()),
                username=DEMO_USERNAME,
                email=DEMO_EMAIL,
                hashed_password=hashed_password,
                full_name="Demo Admin",
                role="admin",
                is_active=True,
                is_superuser=True,
            )
            db.add(new_user)
            db.commit()
            print(f"✅ User '{DEMO_USERNAME}' created successfully!")
        
        print("\n" + "="*50)
        print("Demo Credentials:")
        print(f"  Username: {DEMO_USERNAME}")
        print(f"  Password: {DEMO_PASSWORD}")
        print("="*50 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(create_demo_user())
