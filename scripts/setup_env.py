"""Create .env file from example"""

import shutil
from pathlib import Path

def setup_env():
    """Create .env file from .env.example"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"Created {env_file} from {env_example}")
        print("Please update .env with your configuration")
    elif env_file.exists():
        print(f"{env_file} already exists")
    else:
        print(f"{env_example} not found")


if __name__ == "__main__":
    setup_env()
