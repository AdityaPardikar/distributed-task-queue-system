"""Setup environment file from example"""

import sys
from pathlib import Path
import shutil

def setup_environment():
    """Create .env file from .env.example if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env from .env.example")
        print("⚠️  Please update .env with your database and Redis credentials")
        return True
    else:
        print("✗ .env.example not found")
        return False

if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1)
