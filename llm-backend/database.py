# database.py
import os
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
import hashlib
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Database connection pool
connection_pool = None

def get_database_url():
    """Get database URL from environment variables"""
    # Railway/Production setup
    if os.getenv('DATABASE_URL'):
        return os.getenv('DATABASE_URL')
    
    # Local development setup
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'elimschat_ai')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'password')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def init_connection_pool():
    """Initialize PostgreSQL connection pool"""
    global connection_pool
    try:
        database_url = get_database_url()
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            1, 20,  # min and max connections
            database_url,
            cursor_factory=RealDictCursor
        )
        logger.info("Database connection pool initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        return False

@contextmanager
def get_db_connection():
    """Get database connection from pool"""
    if connection_pool is None:
        init_connection_pool()
    
    connection = None
    try:
        connection = connection_pool.getconn()
        yield connection
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if connection:
            connection_pool.putconn(connection)

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = "rag_chat_app_salt"  # In production, use random salt per user
    return hashlib.sha256((password + salt).encode()).hexdigest()

def init_database():
    """Initialize all database tables"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Users table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    preferred_name VARCHAR(255) NOT NULL,
                    puid VARCHAR(50),
                    role VARCHAR(100) NOT NULL DEFAULT 'user',
                    organization VARCHAR(255),
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    profile_data JSONB
                )''')
                
                # Chat sessions table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )''')
                
                # Chat messages table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL,
                    user_id INTEGER NOT NULL,
                    message_type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    sources JSONB,
                    rating INTEGER,
                    feedback_comment TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )''')
                
                # General feedback table (consolidated from feedback_db)
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS general_feedback (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(36),
                    user_id INTEGER,
                    username VARCHAR(255),
                    query TEXT,
                    source_chunk INTEGER,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    feedback_type VARCHAR(50) DEFAULT 'general',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_general_feedback_user_id ON general_feedback(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_general_feedback_timestamp ON general_feedback(timestamp)')
                
                conn.commit()
                
                # Create default admin user if doesn't exist
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", ('admin',))
                if cursor.fetchone()[0] == 0:
                    create_user(
                        username="admin",
                        email="admin@company.com",
                        password="admin123",
                        full_name="System Administrator",
                        preferred_name="Admin",
                        role="Administrator",
                        organization="IT Department",
                        is_admin=True,
                        puid="P000001"
                    )
                
        logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

# User management functions
def create_user(username: str, email: str, password: str, full_name: str, 
                preferred_name: str, role: str = "user", organization: str = "",
                is_admin: bool = False, puid: str = None) -> bool:
    """Create a new user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                password_hash = hash_password(password)
                utc_now = datetime.utcnow()
                
                # Generate PUID if not provided
                if not puid:
                    puid = f"P{str(uuid.uuid4().int)[:6]}"
                
                cursor.execute("""
                    INSERT INTO users 
                    (username, email, password_hash, full_name, preferred_name, puid, 
                     role, organization, is_admin, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (username, email, password_hash, full_name, preferred_name, puid,
                      role, organization, is_admin, utc_now, utc_now))
                
                conn.commit()
                return True
    except psycopg2.IntegrityError:
        return False  # User already exists
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user data if successful"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                password_hash = hash_password(password)
                
                cursor.execute("""
                    SELECT id, username, email, full_name, preferred_name, puid, 
                           role, organization, is_admin, is_active, created_at
                    FROM users 
                    WHERE username = %s AND password_hash = %s AND is_active = TRUE
                """, (username, password_hash))
                
                user = cursor.fetchone()
                
                if user:
                    # Update last login
                    utc_now = datetime.utcnow()
                    cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", 
                                 (utc_now, user['id']))
                    conn.commit()
                    
                    user_dict = dict(user)
                    # Convert datetime to ISO format string
                    if user_dict.get('created_at'):
                        user_dict['created_at'] = user_dict['created_at'].isoformat()
                    
                    return user_dict
                
                return None
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user data by username"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, username, email, full_name, preferred_name, puid, 
                           role, organization, is_admin, is_active, created_at, 
                           last_login, profile_data
                    FROM users 
                    WHERE username = %s
                """, (username,))
                
                user = cursor.fetchone()
                if user:
                    user_dict = dict(user)
                    # Convert datetime objects to ISO format strings
                    if user_dict.get('created_at'):
                        user_dict['created_at'] = user_dict['created_at'].isoformat()
                    if user_dict.get('last_login'):
                        user_dict['last_login'] = user_dict['last_login'].isoformat()
                    return user_dict
                return None
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None

def update_user_profile(user_id: int, **updates) -> bool:
    """Update user profile fields"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                utc_now = datetime.utcnow()
                
                # Build dynamic UPDATE query
                allowed_fields = ['email', 'full_name', 'preferred_name', 'role', 'organization', 'profile_data']
                update_fields = []
                values = []
                
                for field, value in updates.items():
                    if field in allowed_fields:
                        if field == 'profile_data':
                            value = json.dumps(value) if isinstance(value, dict) else value
                        update_fields.append(f"{field} = %s")
                        values.append(value)
                
                if update_fields:
                    update_fields.append("updated_at = %s")
                    values.append(utc_now)
                    values.append(user_id)
                    
                    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                    cursor.execute(query, values)
                    conn.commit()
                
                return True
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return False

# Chat session functions
def create_chat_session(user_id: int, title: str) -> str:
    """Create a new chat session and return session ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                session_id = str(uuid.uuid4())
                utc_now = datetime.utcnow()
                
                cursor.execute("""
                    INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (session_id, user_id, title, utc_now, utc_now))
                conn.commit()
                
                return session_id
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise

def get_user_chat_sessions(user_id: int) -> List[Dict]:
    """Get all chat sessions for a user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT cs.id, cs.title, cs.created_at, cs.updated_at, cs.is_active,
                           COUNT(cm.id) as message_count,
                           MAX(cm.timestamp) as last_message_time
                    FROM chat_sessions cs
                    LEFT JOIN chat_messages cm ON cs.id = cm.session_id
                    WHERE cs.user_id = %s AND cs.is_active = TRUE
                    GROUP BY cs.id, cs.title, cs.created_at, cs.updated_at, cs.is_active
                    ORDER BY cs.updated_at DESC
                """, (user_id,))
                
                sessions = []
                for row in cursor.fetchall():
                    session_dict = dict(row)
                    # Convert datetime objects to ISO format strings
                    if session_dict.get('created_at'):
                        session_dict['created_at'] = session_dict['created_at'].isoformat()
                    if session_dict.get('updated_at'):
                        session_dict['updated_at'] = session_dict['updated_at'].isoformat()
                    if session_dict.get('last_message_time'):
                        session_dict['last_message_time'] = session_dict['last_message_time'].isoformat()
                    sessions.append(session_dict)
                
                return sessions
    except Exception as e:
        logger.error(f"Error getting user chat sessions: {e}")
        return []

def save_chat_message(session_id: str, user_id: int, message_type: str, 
                     content: str, sources: List[Dict] = None, rating: int = None, 
                     feedback_comment: str = "") -> int:
    """Save a chat message and return message ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                utc_now = datetime.utcnow()
                sources_json = json.dumps(sources) if sources else None
                
                cursor.execute("""
                    INSERT INTO chat_messages 
                    (session_id, user_id, message_type, content, sources, rating, feedback_comment, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (session_id, user_id, message_type, content, sources_json, rating, feedback_comment, utc_now))
                
                message_id = cursor.fetchone()['id']
                
                # Update session updated_at
                cursor.execute("UPDATE chat_sessions SET updated_at = %s WHERE id = %s", 
                             (utc_now, session_id))
                
                conn.commit()
                return message_id
    except Exception as e:
        logger.error(f"Error saving chat message: {e}")
        raise

def get_chat_messages(session_id: str, user_id: int) -> List[Dict]:
    """Get all messages for a chat session"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, message_type, content, sources, rating, feedback_comment, timestamp
                    FROM chat_messages
                    WHERE session_id = %s AND user_id = %s
                    ORDER BY timestamp ASC
                """, (session_id, user_id))
                
                messages = []
                for row in cursor.fetchall():
                    message = dict(row)

                    # Parse sources JSON - support both Postgres JSONB (already parsed to Python objects)
                    # and legacy string JSON stored by other DBs. Preserve list/dict structures.
                    sources_val = message.get('sources')
                    if sources_val:
                        # If DB driver returned a string, parse it
                        if isinstance(sources_val, str):
                            try:
                                message['sources'] = json.loads(sources_val)
                            except Exception:
                                message['sources'] = []
                        # If it's already a dict, wrap in list
                        elif isinstance(sources_val, dict):
                            message['sources'] = [sources_val]
                        # If it's a list, keep as-is
                        elif isinstance(sources_val, list):
                            message['sources'] = sources_val
                        else:
                            message['sources'] = []
                    else:
                        message['sources'] = []

                    # Convert timestamp to ISO format string
                    if message.get('timestamp'):
                        try:
                            message['timestamp'] = message['timestamp'].isoformat()
                        except Exception:
                            # leave as-is if not a datetime
                            pass

                    messages.append(message)

                return messages
    except Exception as e:
        logger.error(f"Error getting chat messages: {e}")
        return []

def update_message_feedback(message_id: int, user_id: int, rating: int, comment: str = "") -> bool:
    """Update feedback for a specific message"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE chat_messages 
                    SET rating = %s, feedback_comment = %s
                    WHERE id = %s AND user_id = %s
                """, (rating, comment, message_id, user_id))
                
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Error updating message feedback: {e}")
        return False

def delete_chat_session(session_id: str, user_id: int) -> bool:
    """Soft delete a chat session"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                utc_now = datetime.utcnow()
                
                cursor.execute("""
                    UPDATE chat_sessions 
                    SET is_active = FALSE, updated_at = %s
                    WHERE id = %s AND user_id = %s
                """, (utc_now, session_id, user_id))
                
                rows_affected = cursor.rowcount
                conn.commit()
                
                return rows_affected > 0
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        return False

def update_session_title(session_id: str, user_id: int, title: str) -> bool:
    """Update chat session title"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                utc_now = datetime.utcnow()
                
                cursor.execute("""
                    UPDATE chat_sessions 
                    SET title = %s, updated_at = %s
                    WHERE id = %s AND user_id = %s
                """, (title, utc_now, session_id, user_id))
                
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Error updating session title: {e}")
        return False

def get_message_details(message_id: int, user_id: int) -> Optional[Dict]:
    """Get details of a specific message for feedback purposes"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT cm.content, cm.session_id, cs.title
                    FROM chat_messages cm
                    LEFT JOIN chat_sessions cs ON cm.session_id = cs.id
                    WHERE cm.id = %s AND cm.user_id = %s AND cm.message_type = 'assistant'
                """, (message_id, user_id))
                
                result = cursor.fetchone()
                return dict(result) if result else None
    except Exception as e:
        logger.error(f"Error getting message details: {e}")
        return None

def get_user_statistics(user_id: int) -> Dict:
    """Get user activity statistics"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get total chat sessions
                cursor.execute("""
                    SELECT COUNT(*) as total_chats FROM chat_sessions 
                    WHERE user_id = %s AND is_active = TRUE
                """, (user_id,))
                total_chats = cursor.fetchone()['total_chats']
                
                # Get total messages sent by user
                cursor.execute("""
                    SELECT COUNT(*) as total_messages FROM chat_messages 
                    WHERE user_id = %s AND message_type = 'user'
                """, (user_id,))
                total_messages = cursor.fetchone()['total_messages']
                
                # Get feedback given (messages with ratings)
                cursor.execute("""
                    SELECT COUNT(*) as feedback_given FROM chat_messages 
                    WHERE user_id = %s AND rating IS NOT NULL
                """, (user_id,))
                feedback_given = cursor.fetchone()['feedback_given']
                
                # Get recent activity
                cursor.execute("""
                    SELECT cm.message_type, cm.content, cm.timestamp, cs.title
                    FROM chat_messages cm
                    JOIN chat_sessions cs ON cm.session_id = cs.id
                    WHERE cm.user_id = %s
                    ORDER BY cm.timestamp DESC
                    LIMIT 10
                """, (user_id,))
                
                recent_activity = []
                for row in cursor.fetchall():
                    message_type, content, timestamp, session_title = row['message_type'], row['content'], row['timestamp'], row['title']
                    
                    if message_type == 'user':
                        action = f"Asked: {content[:50]}..." if len(content) > 50 else f"Asked: {content}"
                    else:
                        action = f"Received AI response in '{session_title}'"
                        
                    try:
                        # Calculate relative time
                        now = datetime.utcnow()
                        diff = now - timestamp
                        
                        if diff.days > 0:
                            time_ago = f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
                        elif diff.seconds > 3600:
                            hours = diff.seconds // 3600
                            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                        elif diff.seconds > 60:
                            minutes = diff.seconds // 60
                            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                        else:
                            time_ago = "Just now"
                            
                    except:
                        time_ago = "Recently"
                        
                    recent_activity.append({
                        "action": action,
                        "time": time_ago
                    })
                
                # Calculate documents viewed (count unique source files from AI responses)
                cursor.execute("""
                    SELECT sources FROM chat_messages 
                    WHERE user_id = %s AND message_type = 'assistant' 
                    AND sources IS NOT NULL AND sources::text != '[]' AND sources::text != 'null'
                """, (user_id,))
                
                unique_documents = set()
                for row in cursor.fetchall():
                    if row['sources']:
                        try:
                            sources = row['sources'] if isinstance(row['sources'], list) else json.loads(row['sources'])
                            for source in sources:
                                if isinstance(source, dict) and 'file' in source:
                                    # Extract filename from path
                                    filename = source['file'].split('/')[-1].split('\\')[-1]
                                    unique_documents.add(filename)
                        except:
                            continue
                documents_viewed = len(unique_documents)
                
                return {
                    "total_chats": total_chats,
                    "total_messages": total_messages,
                    "feedback_given": feedback_given,
                    "documents_viewed": documents_viewed,
                    "recent_activity": recent_activity
                }
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        return {
            "total_chats": 0,
            "total_messages": 0,
            "feedback_given": 0,
            "documents_viewed": 0,
            "recent_activity": []
        }

# General feedback functions (consolidating from feedback_db)
def save_general_feedback(user_id: int = None, username: str = None, session_id: str = None, 
                         query: str = None, source_chunk: int = None, rating: int = None, 
                         comment: str = "", feedback_type: str = "general") -> bool:
    """Save general feedback"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                utc_now = datetime.utcnow()
                
                cursor.execute("""
                    INSERT INTO general_feedback 
                    (session_id, user_id, username, query, source_chunk, rating, comment, feedback_type, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (session_id, user_id, username, query, source_chunk, rating, comment, feedback_type, utc_now))
                
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Error saving general feedback: {e}")
        return False

def get_general_feedbacks(limit: int = 1000) -> List[Dict]:
    """Get general feedback records"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT gf.id, gf.session_id, gf.username, gf.query, gf.source_chunk, 
                           gf.rating, gf.comment, gf.feedback_type, gf.timestamp,
                           u.full_name, u.email
                    FROM general_feedback gf
                    LEFT JOIN users u ON gf.user_id = u.id
                    ORDER BY gf.timestamp DESC 
                    LIMIT %s
                """, (limit,))
                
                feedbacks = []
                for row in cursor.fetchall():
                    feedback = dict(row)
                    feedbacks.append(feedback)
                
                return feedbacks
    except Exception as e:
        logger.error(f"Error getting general feedbacks: {e}")
        return []

# Initialize connection pool on import
init_connection_pool()