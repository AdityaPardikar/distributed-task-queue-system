#!/usr/bin/env python
"""Initialize database from models directly (bypasses Alembic for now)"""

import sys
from src.db.session import engine
from src.models import Base

if __name__ == "__main__":
    print("Creating all tables from models...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)
