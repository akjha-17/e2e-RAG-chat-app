# Updated database functions using unified database system
# This replaces user_db.py and feedback_db.py functionality

import hashlib
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from unified_db import execute_query, get_db_info

# Authentication functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = "rag_chat_app_salt"  # In production, use random salt per user
    return hashlib.sha256((password + salt).encode()).hexdigest()

def create_user(username: str, email: str, password: str, full_name: str, 
                preferred_name: str, organization: str = "", role: str = "user") -> bool:
    """Create a new user"""
    try:
        password_hash = hash_password(password)
        execute_query('''
            INSERT INTO users (username, email, password_hash, full_name, preferred_name, 
                             organization, role, puid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, full_name, preferred_name, organization, role, str(uuid.uuid4())))
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user data"""
    try:
        password_hash = hash_password(password)
        user = execute_query('''
            SELECT * FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = TRUE
        ''', (username, password_hash), fetch_one=True)
        
        if user:
            # Update last login
            execute_query('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user['id'],))
            
        return user
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username"""
    try:
        return execute_query('''
            SELECT * FROM users WHERE username = ?
        ''', (username,), fetch_one=True)
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def update_user_profile(user_id: int, updates: Dict) -> bool:
    """Update user profile"""
    try:
        # Build dynamic update query
        set_clauses = []
        values = []
        
        allowed_fields = ['full_name', 'preferred_name', 'email', 'organization', 'profile_data']
        for field, value in updates.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = ?")
                values.append(json.dumps(value) if field == 'profile_data' and isinstance(value, dict) else value)
        
        if not set_clauses:
            return False
            
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        execute_query(query, tuple(values))
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False

# Chat session functions
def create_chat_session(user_id: int, title: str = "New Chat") -> str:
    """Create a new chat session"""
    try:
        session_id = str(uuid.uuid4())
        execute_query('''
            INSERT INTO chat_sessions (id, user_id, title)
            VALUES (?, ?, ?)
        ''', (session_id, user_id, title))
        return session_id
    except Exception as e:
        print(f"Error creating chat session: {e}")
        return ""

def get_user_chat_sessions(user_id: int) -> List[Dict]:
    """Get all chat sessions for a user"""
    try:
        return execute_query('''
            SELECT * FROM chat_sessions 
            WHERE user_id = ? AND is_active = TRUE 
            ORDER BY updated_at DESC
        ''', (user_id,), fetch_all=True) or []
    except Exception as e:
        print(f"Error getting chat sessions: {e}")
        return []

def update_session_title(session_id: str, user_id: int, title: str) -> bool:
    """Update chat session title"""
    try:
        execute_query('''
            UPDATE chat_sessions 
            SET title = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND user_id = ?
        ''', (title, session_id, user_id))
        return True
    except Exception as e:
        print(f"Error updating session title: {e}")
        return False

def delete_chat_session(session_id: str, user_id: int) -> bool:
    """Delete a chat session (soft delete)"""
    try:
        execute_query('''
            UPDATE chat_sessions 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND user_id = ?
        ''', (session_id, user_id))
        return True
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        return False

# Chat message functions
def save_chat_message(session_id: str, user_id: int, message_type: str, 
                     content: str, sources: List[Dict] = None) -> int:
    """Save a chat message"""
    try:
        sources_json = json.dumps(sources) if sources else None
        result = execute_query('''
            INSERT INTO chat_messages (session_id, user_id, message_type, content, sources)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, message_type, content, sources_json))
        
        # Update session timestamp
        execute_query('''
            UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (session_id,))
        
        return result
    except Exception as e:
        print(f"Error saving chat message: {e}")
        return 0

def get_chat_messages(session_id: str, user_id: int) -> List[Dict]:
    """Get all messages for a chat session"""
    try:
        messages = execute_query('''
            SELECT * FROM chat_messages 
            WHERE session_id = ? AND user_id = ? 
            ORDER BY created_at ASC
        ''', (session_id, user_id), fetch_all=True) or []
        
        # Parse sources JSON
        for message in messages:
            if message.get('sources'):
                try:
                    message['sources'] = json.loads(message['sources'])
                except:
                    message['sources'] = []
                    
        return messages
    except Exception as e:
        print(f"Error getting chat messages: {e}")
        return []

def update_message_feedback(message_id: int, user_id: int, rating: int, comment: str = "") -> bool:
    """Update feedback for a message"""
    try:
        execute_query('''
            UPDATE chat_messages 
            SET feedback_rating = ?, feedback_comment = ? 
            WHERE id = ? AND user_id = ?
        ''', (rating, comment, message_id, user_id))
        return True
    except Exception as e:
        print(f"Error updating message feedback: {e}")
        return False

# Feedback functions (unified from feedback_db.py)
def save_feedback(user_id: int, session_id: str, query: str, source_chunk: int = None, 
                 rating: int = None, comment: str = "", feedback_type: str = "rating", 
                 message_id: int = None) -> bool:
    """Save user feedback"""
    try:
        execute_query('''
            INSERT INTO feedback (user_id, session_id, message_id, query, source_chunk, 
                                rating, comment, feedback_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, session_id, message_id, query, source_chunk, rating, comment, feedback_type))
        return True
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return False

def get_feedbacks(user_id: int = None, session_id: str = None) -> List[Dict]:
    """Get feedback data with optional filters"""
    try:
        if user_id and session_id:
            return execute_query('''
                SELECT * FROM feedback 
                WHERE user_id = ? AND session_id = ? 
                ORDER BY created_at DESC
            ''', (user_id, session_id), fetch_all=True) or []
        elif user_id:
            return execute_query('''
                SELECT * FROM feedback 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,), fetch_all=True) or []
        else:
            return execute_query('''
                SELECT * FROM feedback 
                ORDER BY created_at DESC
            ''', fetch_all=True) or []
    except Exception as e:
        print(f"Error getting feedback: {e}")
        return []

# Statistics and analytics
def get_user_statistics(user_id: int) -> Dict[str, Any]:
    """Get user activity statistics"""
    try:
        stats = {
            "total_chats": 0,
            "total_messages": 0,
            "feedback_given": 0,
            "documents_viewed": 0,
            "recent_activity": []
        }
        
        # Get chat count
        chat_count = execute_query('''
            SELECT COUNT(*) as count FROM chat_sessions 
            WHERE user_id = ? AND is_active = TRUE
        ''', (user_id,), fetch_one=True)
        stats["total_chats"] = chat_count["count"] if chat_count else 0
        
        # Get message count
        message_count = execute_query('''
            SELECT COUNT(*) as count FROM chat_messages WHERE user_id = ?
        ''', (user_id,), fetch_one=True)
        stats["total_messages"] = message_count["count"] if message_count else 0
        
        # Get feedback count
        feedback_count = execute_query('''
            SELECT COUNT(*) as count FROM feedback WHERE user_id = ?
        ''', (user_id,), fetch_one=True)
        stats["feedback_given"] = feedback_count["count"] if feedback_count else 0
        
        # Get recent activity
        recent = execute_query('''
            SELECT title, updated_at FROM chat_sessions 
            WHERE user_id = ? AND is_active = TRUE 
            ORDER BY updated_at DESC LIMIT 5
        ''', (user_id,), fetch_all=True)
        stats["recent_activity"] = recent or []
        
        return stats
    except Exception as e:
        print(f"Error getting user statistics: {e}")
        return {"total_chats": 0, "total_messages": 0, "feedback_given": 0, "documents_viewed": 0, "recent_activity": []}

# Database info function
def get_message_details(message_id: int, user_id: int) -> Optional[Dict]:
    """Get specific message details"""
    try:
        return execute_query('''
            SELECT * FROM chat_messages 
            WHERE id = ? AND user_id = ?
        ''', (message_id, user_id), fetch_one=True)
    except Exception as e:
        print(f"Error getting message details: {e}")
        return None

def get_database_status() -> Dict[str, Any]:
    """Get current database status and info"""
    try:
        info = get_db_info()
        
        # Get table counts
        tables = ['users', 'chat_sessions', 'chat_messages', 'feedback']
        counts = {}
        
        for table in tables:
            try:
                result = execute_query(f'SELECT COUNT(*) as count FROM {table}', fetch_one=True)
                counts[table] = result['count'] if result else 0
            except:
                counts[table] = 0
        
        return {
            **info,
            "table_counts": counts,
            "status": "connected"
        }
    except Exception as e:
        return {
            "type": "unknown",
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    # Test database functions
    print("🧪 Testing unified database functions...")
    
    status = get_database_status()
    print(f"Database Status: {status}")
    
    # Test user creation (if no users exist)
    if status.get("table_counts", {}).get("users", 0) == 0:
        print("Creating test user...")
        success = create_user("testuser", "test@example.com", "password123", 
                            "Test User", "Tester", "Test Org")
        print(f"User creation: {'Success' if success else 'Failed'}")
        
        if success:
            user = authenticate_user("testuser", "password123")
            print(f"User authentication: {'Success' if user else 'Failed'}")
            
            if user:
                session_id = create_chat_session(user['id'], "Test Chat Session")
                print(f"Chat session created: {session_id}")
                
                if session_id:
                    message_result = save_chat_message(session_id, user['id'], "user", "Hello, world!")
                    print(f"Message saved: {'Success' if message_result else 'Failed'}")
                    
                    feedback_result = save_feedback(user['id'], session_id, "Test query", rating=5, comment="Great!")
                    print(f"Feedback saved: {'Success' if feedback_result else 'Failed'}")
    
    print("✅ Database functions test complete!")