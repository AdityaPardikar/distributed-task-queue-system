"""Development environment setup script"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and return success status"""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description}")
            return True
        else:
            print(f"✗ {description}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {description}: {e}")
        return False

def setup_dev_environment():
    """Complete development environment setup"""
    print("=" * 60)
    print("TaskFlow Development Environment Setup")
    print("=" * 60)
    
    steps = [
        ("python -m venv venv", "Creating virtual environment"),
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing dependencies"),
        ("pip install -r requirements-dev.txt", "Installing dev dependencies"),
        ("python scripts/init_env.py", "Setting up environment file"),
        ("python scripts/init_db.py", "Initializing database"),
    ]
    
    all_success = True
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            all_success = False
            break
    
    print("\n" + "=" * 60)
    if all_success:
        print("✓ Development environment ready!")
        print("\nNext steps:")
        print("1. Update .env with your database credentials")
        print("2. Start Docker services: docker-compose up -d")
        print("3. Run API server: python run.py")
    else:
        print("✗ Setup failed. Please check the errors above.")
    print("=" * 60)
    
    return all_success

if __name__ == "__main__":
    success = setup_dev_environment()
    sys.exit(0 if success else 1)
