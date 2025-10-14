# user_db.py
import sqlite3
import hashlib
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from config import BASE_DIR

DB_PATH = Path(BASE_DIR) / "users.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = "rag_chat_app_salt"  # In production, use random salt per user
    return hashlib.sha256((password + salt).encode()).hexdigest()

def init_user_db():
    """Initialize user database with users, chat_sessions, and chat_messages tables"""
    conn = _conn()
    
    # Users table
    conn.execute('''
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
        profile_data TEXT  -- JSON field for additional profile info
    )''')
    
    # Chat sessions table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,  -- UUID
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )''')
    
    # Chat messages table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        message_type TEXT NOT NULL,  -- 'user' or 'assistant'
        content TEXT NOT NULL,
        sources TEXT,  -- JSON field for source information
        rating INTEGER,
        feedback_comment TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )''')
    
    conn.commit()
    
    # Create default admin user if doesn't exist
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
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
    
    conn.close()

def create_user(username: str, email: str, password: str, full_name: str, 
                preferred_name: str, role: str = "user", organization: str = "",
                is_admin: bool = False, puid: str = None) -> bool:
    """Create a new user"""
    try:
        conn = _conn()
        password_hash = hash_password(password)
        utc_now = datetime.utcnow().isoformat()
        
        # Generate PUID if not provided
        if not puid:
            puid = f"P{str(uuid.uuid4().int)[:6]}"
        
        conn.execute("""
            INSERT INTO users 
            (username, email, password_hash, full_name, preferred_name, puid, 
             role, organization, is_admin, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, email, password_hash, full_name, preferred_name, puid,
              role, organization, is_admin, utc_now, utc_now))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # User already exists

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user data if successful"""
    conn = _conn()
    password_hash = hash_password(password)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, email, full_name, preferred_name, puid, 
               role, organization, is_admin, is_active, created_at
        FROM users 
        WHERE username = ? AND password_hash = ? AND is_active = TRUE
    """, (username, password_hash))
    
    user = cursor.fetchone()
    
    if user:
        # Update last login
        utc_now = datetime.utcnow().isoformat()
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (utc_now, user[0]))
        conn.commit()
        
        user_data = {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "full_name": user[3],
            "preferred_name": user[4],
            "puid": user[5],
            "role": user[6],
            "organization": user[7],
            "is_admin": bool(user[8]),
            "is_active": bool(user[9]),
            "created_at": user[10]
        }
        conn.close()
        return user_data
    
    conn.close()
    return None

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user data by username"""
    conn = _conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, full_name, preferred_name, puid, 
               role, organization, is_admin, is_active, created_at, 
               last_login, profile_data
        FROM users 
        WHERE username = ?
    """, (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        profile_data = {}
        if user[12]:  # profile_data column
            try:
                profile_data = json.loads(user[12])
            except:
                profile_data = {}
                
        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "full_name": user[3],
            "preferred_name": user[4],
            "puid": user[5],
            "role": user[6],
            "organization": user[7],
            "is_admin": bool(user[8]),
            "is_active": bool(user[9]),
            "created_at": user[10],
            "last_login": user[11],
            "profile_data": profile_data
        }
    return None

def update_user_profile(user_id: int, **updates) -> bool:
    """Update user profile fields"""
    try:
        conn = _conn()
        utc_now = datetime.utcnow().isoformat()
        
        # Build dynamic UPDATE query
        allowed_fields = ['email', 'full_name', 'preferred_name', 'role', 'organization', 'profile_data']
        update_fields = []
        values = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                if field == 'profile_data':
                    value = json.dumps(value) if isinstance(value, dict) else value
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if update_fields:
            update_fields.append("updated_at = ?")
            values.append(utc_now)
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(query, values)
            conn.commit()
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False

def create_chat_session(user_id: int, title: str) -> str:
    """Create a new chat session and return session ID"""
    session_id = str(uuid.uuid4())
    utc_now = datetime.utcnow().isoformat()
    
    conn = _conn()
    conn.execute("""
        INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, user_id, title, utc_now, utc_now))
    conn.commit()
    conn.close()
    
    return session_id

def get_user_chat_sessions(user_id: int) -> List[Dict]:
    """Get all chat sessions for a user"""
    conn = _conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT cs.id, cs.title, cs.created_at, cs.updated_at, cs.is_active,
               COUNT(cm.id) as message_count,
               MAX(cm.timestamp) as last_message_time
        FROM chat_sessions cs
        LEFT JOIN chat_messages cm ON cs.id = cm.session_id
        WHERE cs.user_id = ? AND cs.is_active = TRUE
        GROUP BY cs.id, cs.title, cs.created_at, cs.updated_at, cs.is_active
        ORDER BY cs.updated_at DESC
    """, (user_id,))
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            "id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
            "is_active": bool(row[4]),
            "message_count": row[5] or 0,
            "last_message_time": row[6]
        })
    
    conn.close()
    return sessions

def save_chat_message(session_id: str, user_id: int, message_type: str, 
                     content: str, sources: List[Dict] = None, rating: int = None, 
                     feedback_comment: str = "") -> int:
    """Save a chat message and return message ID"""
    utc_now = datetime.utcnow().isoformat()
    sources_json = json.dumps(sources) if sources else None
    
    conn = _conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO chat_messages 
        (session_id, user_id, message_type, content, sources, rating, feedback_comment, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, user_id, message_type, content, sources_json, rating, feedback_comment, utc_now))
    
    message_id = cursor.lastrowid
    
    # Update session updated_at
    conn.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (utc_now, session_id))
    
    conn.commit()
    conn.close()
    
    return message_id

def get_chat_messages(session_id: str, user_id: int) -> List[Dict]:
    """Get all messages for a chat session"""
    conn = _conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, message_type, content, sources, rating, feedback_comment, timestamp
        FROM chat_messages
        WHERE session_id = ? AND user_id = ?
        ORDER BY timestamp ASC
    """, (session_id, user_id))
    
    messages = []
    for row in cursor.fetchall():
        sources = []
        if row[3]:  # sources column
            try:
                sources = json.loads(row[3])
            except:
                sources = []
                
        messages.append({
            "id": row[0],
            "message_type": row[1],
            "content": row[2],
            "sources": sources,
            "rating": row[4],
            "feedback_comment": row[5] or "",
            "timestamp": row[6]
        })
    
    conn.close()
    return messages

def update_message_feedback(message_id: int, user_id: int, rating: int, comment: str = "") -> bool:
    """Update feedback for a specific message"""
    try:
        conn = _conn()
        conn.execute("""
            UPDATE chat_messages 
            SET rating = ?, feedback_comment = ?
            WHERE id = ? AND user_id = ?
        """, (rating, comment, message_id, user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating message feedback: {e}")
        return False

def delete_chat_session(session_id: str, user_id: int) -> bool:
    """Soft delete a chat session"""
    try:
        conn = _conn()
        utc_now = datetime.utcnow().isoformat()
        
        print(f"[DELETE] Attempting to delete session {session_id} for user {user_id}")
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chat_sessions 
            SET is_active = FALSE, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (utc_now, session_id, user_id))
        
        rows_affected = cursor.rowcount
        print(f"[DELETE] Rows affected: {rows_affected}")
        
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            print(f"[DELETE] Successfully deleted session {session_id}")
            return True
        else:
            print(f"[DELETE] No session found with id {session_id} for user {user_id}")
            return False
            
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        return False

def update_session_title(session_id: str, user_id: int, title: str) -> bool:
    """Update chat session title"""
    try:
        conn = _conn()
        utc_now = datetime.utcnow().isoformat()
        
        conn.execute("""
            UPDATE chat_sessions 
            SET title = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (title, utc_now, session_id, user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating session title: {e}")
        return False

def get_message_details(message_id: int, user_id: int) -> Optional[Dict]:
    """Get details of a specific message for feedback purposes"""
    conn = _conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT cm.content, cm.session_id, cs.title
            FROM chat_messages cm
            LEFT JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cm.id = ? AND cm.user_id = ? AND cm.message_type = 'assistant'
        """, (message_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "content": result[0],
                "session_id": result[1],
                "session_title": result[2]
            }
        return None
        
    except Exception as e:
        print(f"Error getting message details: {e}")
        conn.close()
        return None

def get_user_statistics(user_id: int) -> Dict:
    """Get user activity statistics"""
    conn = _conn()
    cursor = conn.cursor()
    
    try:
        # Get total chat sessions
        cursor.execute("""
            SELECT COUNT(*) FROM chat_sessions 
            WHERE user_id = ? AND is_active = TRUE
        """, (user_id,))
        total_chats = cursor.fetchone()[0]
        
        # Get total messages sent by user
        cursor.execute("""
            SELECT COUNT(*) FROM chat_messages 
            WHERE user_id = ? AND message_type = 'user'
        """, (user_id,))
        total_messages = cursor.fetchone()[0]
        
        # Get feedback given (messages with ratings)
        cursor.execute("""
            SELECT COUNT(*) FROM chat_messages 
            WHERE user_id = ? AND rating IS NOT NULL
        """, (user_id,))
        feedback_given = cursor.fetchone()[0]
        
        # Get recent activity (last 10 actions)
        cursor.execute("""
            SELECT cm.message_type, cm.content, cm.timestamp, cs.title
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cm.user_id = ?
            ORDER BY cm.timestamp DESC
            LIMIT 10
        """, (user_id,))
        
        recent_activity = []
        for row in cursor.fetchall():
            message_type, content, timestamp, session_title = row
            
            if message_type == 'user':
                action = f"Asked: {content[:50]}..." if len(content) > 50 else f"Asked: {content}"
            else:
                action = f"Received AI response in '{session_title}'"
                
            try:
                # Parse timestamp and calculate relative time
                msg_time = datetime.fromisoformat(timestamp.replace('Z', ''))
                now = datetime.utcnow()
                diff = now - msg_time
                
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
            SELECT cm.sources FROM chat_messages cm
            WHERE cm.user_id = ? AND cm.message_type = 'assistant' 
            AND cm.sources IS NOT NULL AND cm.sources != '[]' AND cm.sources != 'null'
        """, (user_id,))
        
        unique_documents = set()
        for (sources_json,) in cursor.fetchall():
            if sources_json:
                try:
                    sources = json.loads(sources_json)
                    for source in sources:
                        if isinstance(source, dict) and 'file' in source:
                            # Extract filename from path
                            filename = source['file'].split('/')[-1].split('\\')[-1]
                            unique_documents.add(filename)
                except:
                    continue
        documents_viewed = len(unique_documents)
        
        conn.close()
        
        return {
            "total_chats": total_chats,
            "total_messages": total_messages,
            "feedback_given": feedback_given,
            "documents_viewed": documents_viewed,
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        print(f"Error getting user statistics: {e}")
        conn.close()
        return {
            "total_chats": 0,
            "total_messages": 0,
            "feedback_given": 0,
            "documents_viewed": 0,
            "recent_activity": []
        }

# Initialize the database
init_user_db()