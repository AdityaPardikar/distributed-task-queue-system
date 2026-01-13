"""Initialize database and create tables"""

from src.db.session import init_db, engine
from src.models import Base


def setup_database():
    """Create all database tables"""
    print("Creating database tables...")
    init_db()
    print("Database tables created successfully!")


if __name__ == "__main__":
    setup_database()
