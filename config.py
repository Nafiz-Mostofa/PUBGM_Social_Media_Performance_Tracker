import os
from pathlib import Path
from dotenv import load_dotenv

# Calculate the dynamic project root base on this file's position
# regardless of where it's executed from or the folder name
BASE_DIR = Path(__file__).resolve().parent

# Load the environment variables from the absolute path to the .env file
env_path = BASE_DIR / ".env"

def init_setup():
    """Central configuration loader to be called by entry points."""
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # Fallback to local working directory if .env not in root
        load_dotenv()
