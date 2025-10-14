# app/feedback_db.py
import sqlite3
from pathlib import Path
from datetime import datetime
from config import BASE_DIR

DB_PATH = Path(BASE_DIR) / "feedback.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)

def init_db():
    conn = _conn()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        user TEXT,
        query TEXT,
        source_chunk INTEGER,
        rating INTEGER,
        comment TEXT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def save_feedback(user, session_id, query, source_chunk, rating, comment=""):
    """Save feedback with explicit UTC timestamp"""
    conn = _conn()
    # Use explicit UTC timestamp
    utc_now = datetime.utcnow().isoformat()
    conn.execute("INSERT INTO feedback(session_id, user, query, source_chunk, rating, comment, ts) VALUES(?,?,?,?,?,?,?)",
                 (session_id, user, query, source_chunk, rating, comment, utc_now))
    conn.commit()
    conn.close()

# Fetch all feedback records (optionally with filters in the future)
def get_feedbacks(limit=1000):
    """Get feedbacks with consistent timestamp format"""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT id, session_id, user, query, source_chunk, rating, comment, ts FROM feedback ORDER BY ts DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    
    # Return as list of dicts with consistent field names for frontend
    results = []
    for row in rows:
        feedback = {
            "id": row[0],
            "session_id": row[1], 
            "username": row[2],  # Map 'user' to 'username' for frontend consistency
            "query": row[3],
            "source_chunk": row[4],
            "rating": row[5],
            "comment": row[6],
            "timestamp": row[7]  # Keep as is - should be UTC ISO format
        }
        results.append(feedback)
    
    return results

init_db()
