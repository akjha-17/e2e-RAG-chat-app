# Database configuration with dual support
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.resolve()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/users.db")

# Fix Railway PostgreSQL URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

# Database type detection
DB_TYPE = "postgresql" if "postgresql://" in DATABASE_URL else "sqlite"

print(f"🗄️ Database Type: {DB_TYPE}")
print(f"🔗 Database URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else DATABASE_URL)