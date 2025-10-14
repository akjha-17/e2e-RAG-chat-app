#!/usr/bin/env python3
"""
Database inspection script for the chat application
Usage: python db_inspect.py
"""
import sqlite3
import json
from datetime import datetime

def inspect_database(db_file="users.db"):
    """Inspect the SQLite database and show schema and sample data"""
    db_path = db_file
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("DATABASE INSPECTION REPORT")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 TABLES FOUND: {len(tables)}")
        for table in tables:
            print(f"  • {table[0]}")
        
        # Inspect each table
        for table in tables:
            table_name = table[0]
            print(f"\n{'='*50}")
            print(f"TABLE: {table_name.upper()}")
            print(f"{'='*50}")
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("\n📊 SCHEMA:")
            print("Column Name      | Type         | Not Null | Default | PK")
            print("-" * 55)
            for col in columns:
                name = col[1].ljust(16)
                dtype = col[2].ljust(12)
                notnull = "YES" if col[3] else "NO"
                default = str(col[4]) if col[4] else "NULL"
                pk = "YES" if col[5] else "NO"
                print(f"{name} | {dtype} | {notnull.ljust(8)} | {default.ljust(7)} | {pk}")
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"\n📈 RECORD COUNT: {count}")
            
            # Show sample records (limit to 5)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                records = cursor.fetchall()
                
                print(f"\n📋 SAMPLE RECORDS (up to 5):")
                col_names = [col[1] for col in columns]
                
                # Print headers
                header = " | ".join([name[:15].ljust(15) for name in col_names])
                print(header)
                print("-" * len(header))
                
                # Print records
                for record in records:
                    row_data = []
                    for i, value in enumerate(record):
                        if value is None:
                            display_value = "NULL"
                        elif isinstance(value, str) and len(value) > 15:
                            display_value = value[:12] + "..."
                        else:
                            display_value = str(value)
                        row_data.append(display_value.ljust(15))
                    
                    print(" | ".join(row_data))
        
        # Show some useful queries
        print(f"\n{'='*60}")
        print("USEFUL QUERIES")
        print(f"{'='*60}")
        
        # User statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN is_admin = 1 THEN 1 ELSE 0 END) as admin_users,
                SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as regular_users
            FROM users
        """)
        user_stats = cursor.fetchone()
        if user_stats[0] > 0:
            print(f"\n👥 USER STATISTICS:")
            print(f"  Total Users: {user_stats[0]}")
            print(f"  Admin Users: {user_stats[1]}")
            print(f"  Regular Users: {user_stats[2]}")
        
        # Chat session statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                COUNT(DISTINCT user_id) as users_with_sessions
            FROM chat_sessions
        """)
        session_stats = cursor.fetchone()
        if session_stats[0] > 0:
            print(f"\n💬 CHAT SESSION STATISTICS:")
            print(f"  Total Sessions: {session_stats[0]}")
            print(f"  Users with Sessions: {session_stats[1]}")
        
        # Message statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_messages,
                SUM(CASE WHEN message_type = 'user' THEN 1 ELSE 0 END) as user_messages,
                SUM(CASE WHEN message_type = 'assistant' THEN 1 ELSE 0 END) as ai_messages
            FROM chat_messages
        """)
        message_stats = cursor.fetchone()
        if message_stats[0] > 0:
            print(f"\n📝 MESSAGE STATISTICS:")
            print(f"  Total Messages: {message_stats[0]}")
            print(f"  User Messages: {message_stats[1]}")
            print(f"  AI Messages: {message_stats[2]}")
        
        # Recent activity
        cursor.execute("""
            SELECT u.username, cs.title, cs.created_at
            FROM chat_sessions cs
            JOIN users u ON cs.user_id = u.id
            ORDER BY cs.created_at DESC
            LIMIT 5
        """)
        recent_sessions = cursor.fetchall()
        
        if recent_sessions:
            print(f"\n🕒 RECENT CHAT SESSIONS:")
            for session in recent_sessions:
                username = session[0]
                title = session[1][:30] + "..." if len(session[1]) > 30 else session[1]
                created_at = session[2]
                print(f"  {username}: {title} ({created_at})")
        
        conn.close()
        
        print(f"\n{'='*60}")
        print("✅ Database inspection completed successfully!")
        print(f"{'='*60}")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    print("Available databases:")
    print("1. users.db (User management, chat sessions, messages)")
    print("2. feedback.db (Legacy feedback system)")
    
    if len(sys.argv) > 1:
        db_file = sys.argv[1]
    else:
        db_file = "users.db"  # Default to users.db
    
    print(f"\n🔍 Inspecting: {db_file}")
    inspect_database(db_file)