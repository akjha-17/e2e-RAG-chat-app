# Database adapter for SQLite + PostgreSQL compatibility
import os
import sqlite3
from pathlib import Path
from config import BASE_DIR

# Check if we have a PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL", "")

def get_connection():
    """Get database connection - works with both SQLite and PostgreSQL"""
    
    if DATABASE_URL and "postgresql://" in DATABASE_URL:
        # Production: Use PostgreSQL
        try:
            import psycopg2
            # Fix Railway URL format
            url = DATABASE_URL.replace("postgres://", "postgresql://")
            conn = psycopg2.connect(url)
            return conn, "postgresql"
        except ImportError:
            print("⚠️ psycopg2 not installed, falling back to SQLite")
        except Exception as e:
            print(f"⚠️ PostgreSQL connection big failure: {e}, falling back to SQLite")
    
    # Development: Use SQLite (default)
    db_path = Path(BASE_DIR) / "users.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    return conn, "sqlite"

def execute_sql(query, params=None, fetch_one=False, fetch_all=False):
    """Execute SQL with automatic connection handling"""
    conn, db_type = get_connection()
    
    try:
        if db_type == "postgresql":
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                
                conn.commit()
                return cursor.rowcount
        else:
            # SQLite
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
                conn.close()
                return result
            elif fetch_all:
                result = cursor.fetchall()
                conn.close()
                return result
                
            conn.commit()
            rowcount = cursor.rowcount
            conn.close()
            return rowcount
            
    except Exception as e:
        print(f"Database error: {e}")
        if conn:
            conn.close()
        raise

# Test database connection
if __name__ == "__main__":
    try:
        conn, db_type = get_connection()
        print(f"✅ Database connection successful: {db_type}")
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")