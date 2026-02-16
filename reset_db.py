#!/usr/bin/env python
"""Drop all tables and recreate them with new schema"""

import sys
from src.db.session import engine
from src.models import Base

if __name__ == "__main__":
    print("Dropping all existing tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped successfully!")
    except Exception as e:
        print(f"⚠️  Error dropping tables: {e}")
    
    print("\nCreating all tables from models...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)
