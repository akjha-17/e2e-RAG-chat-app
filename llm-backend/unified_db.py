# Unified Database System - SQLite (dev) + PostgreSQL (production)
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Union
from config import BASE_DIR

# Environment detection
IS_PRODUCTION = bool(os.getenv("DATABASE_URL")) or bool(os.getenv("RAILWAY_ENVIRONMENT"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

class DatabaseManager:
    """Unified database manager supporting both SQLite and PostgreSQL"""
    
    def __init__(self):
        self.db_type = "postgresql" if DATABASE_URL and "postgresql" in DATABASE_URL else "sqlite"
        self.is_production = IS_PRODUCTION
        
        if self.db_type == "sqlite":
            self.db_path = Path(BASE_DIR) / "unified_app.db"
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"🗄️ Using SQLite: {self.db_path}")
        else:
            print(f"🗄️ Using PostgreSQL: {DATABASE_URL[:50]}...")
    
    def get_connection(self):
        """Get database connection based on environment"""
        if self.db_type == "postgresql":
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                # Fix Railway URL format
                url = DATABASE_URL.replace("postgres://", "postgresql://")
                conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
                return conn
            except ImportError:
                raise Exception("psycopg2 not installed for PostgreSQL support")
        else:
            # SQLite with Row factory for dict-like access
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
    
    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False) -> Any:
        """Execute query with automatic connection handling"""
        conn = self.get_connection()
        
        try:
            if self.db_type == "postgresql":
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    
                    if fetch_one:
                        result = cursor.fetchone()
                        conn.commit()
                        return dict(result) if result else None
                    elif fetch_all:
                        results = cursor.fetchall()
                        conn.commit()
                        return [dict(row) for row in results]
                    
                    conn.commit()
                    return cursor.rowcount
            else:
                # SQLite
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch_one:
                    result = cursor.fetchone()
                    conn.commit()
                    conn.close()
                    return dict(result) if result else None
                elif fetch_all:
                    results = cursor.fetchall()
                    conn.commit()
                    conn.close()
                    return [dict(row) for row in results]
                
                conn.commit()
                rowcount = cursor.rowcount
                conn.close()
                return rowcount
                
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            raise e
    
    def init_database(self):
        """Initialize all database tables"""
        print(f"🔧 Initializing {self.db_type} database...")
        
        # Users table
        users_sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            preferred_name VARCHAR(255) NOT NULL,
            puid VARCHAR(255),
            role VARCHAR(50) NOT NULL DEFAULT 'user',
            organization VARCHAR(255),
            is_admin BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            profile_data TEXT
        )''' if self.db_type == "postgresql" else '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            preferred_name TEXT NOT NULL,
            puid TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            organization TEXT,
            is_admin BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            profile_data TEXT
        )'''
        
        # Chat sessions table
        sessions_sql = '''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id VARCHAR(255) PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(500) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            session_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''' if self.db_type == "postgresql" else '''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            session_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )'''
        
        # Chat messages table
        messages_sql = '''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            user_id INTEGER NOT NULL,
            message_type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            feedback_rating INTEGER,
            feedback_comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''' if self.db_type == "postgresql" else '''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            feedback_rating INTEGER,
            feedback_comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )'''
        
        # Unified feedback table (replaces separate feedback.db)
        feedback_sql = '''
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255),
            user_id INTEGER,
            message_id INTEGER,
            query TEXT,
            source_chunk INTEGER,
            rating INTEGER,
            comment TEXT,
            feedback_type VARCHAR(50) DEFAULT 'rating',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (message_id) REFERENCES chat_messages(id)
        )''' if self.db_type == "postgresql" else '''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id INTEGER,
            message_id INTEGER,
            query TEXT,
            source_chunk INTEGER,
            rating INTEGER,
            comment TEXT,
            feedback_type TEXT DEFAULT 'rating',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (message_id) REFERENCES chat_messages(id)
        )'''
        
        # Execute all table creation
        tables = [users_sql, sessions_sql, messages_sql, feedback_sql]
        for sql in tables:
            try:
                self.execute_query(sql)
                print(f"✅ Table created/verified")
            except Exception as e:
                print(f"❌ Error creating table: {e}")
                raise
        
        print(f"🎉 Database initialization complete!")

# Global database manager instance
db = DatabaseManager()

# Initialize database on import
try:
    db.init_database()
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")
    print("This is normal if psycopg2 isn't installed locally")

# Convenience functions
def execute_query(*args, **kwargs):
    """Convenience function to execute queries"""
    return db.execute_query(*args, **kwargs)

def get_db_info():
    """Get current database information"""
    return {
        "type": db.db_type,
        "is_production": db.is_production,
        "path": str(db.db_path) if db.db_type == "sqlite" else "PostgreSQL Cloud"
    }

if __name__ == "__main__":
    # Test database connection
    print("🧪 Testing database connection...")
    info = get_db_info()
    print(f"Database Type: {info['type']}")
    print(f"Is Production: {info['is_production']}")
    print(f"Location: {info['path']}")