"""Alembic initialization"""

from alembic import command
from alembic.config import Config

def init_alembic():
    """Initialize Alembic migrations"""
    config = Config("alembic.ini")
    command.init(config, "src/db/migrations", template="generic")
    print("Alembic initialized")

if __name__ == "__main__":
    init_alembic()
