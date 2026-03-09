import os
from dotenv import load_dotenv

load_dotenv()

# Default location (Jaipur coordinates for demo)
DEFAULT_LAT = 26.8500
DEFAULT_LNG = 75.8200

# API Settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smarter_blinkit")
