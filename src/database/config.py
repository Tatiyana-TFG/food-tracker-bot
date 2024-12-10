import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = Path('src') / 'database' / 'database' / 'nutrition.db'



# Ensure database directory exists
DATABASE_PATH.parent.mkdir(exist_ok=True)