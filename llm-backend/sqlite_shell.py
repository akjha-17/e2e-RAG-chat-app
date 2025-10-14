#!/usr/bin/env python3
"""
Interactive SQLite shell using Python
Usage: python sqlite_shell.py [database_file]
"""
import sqlite3
import sys

def interactive_shell(db_file="users.db"):
    """Start an interactive SQLite shell"""
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print(f"🗄️  Connected to: {db_file}")
        print("📋 Type SQL commands or special commands:")
        print("   .help     - Show this help")
        print("   .tables   - List all tables")
        print("   .schema   - Show all schemas")
        print("   .schema [table] - Show table schema")
        print("   .quit     - Exit")
        print("   SQL commands end with ';'")
        print("-" * 50)
        
        while True:
            try:
                # Get user input
                query = input("sqlite> ").strip()
                
                if not query:
                    continue
                    
                # Handle special commands
                if query.startswith('.'):
                    if query == '.quit' or query == '.exit':
                        break
                    elif query == '.help':
                        print("📋 Special Commands:")
                        print("   .tables   - List all tables")
                        print("   .schema   - Show all schemas") 
                        print("   .schema [table] - Show table schema")
                        print("   .quit     - Exit")
                        print("📋 SQL Commands (end with ';'):")
                        print("   SELECT * FROM users;")
                        print("   SELECT COUNT(*) FROM chat_sessions;")
                        print("   SELECT username, created_at FROM users;")
                        continue
                    elif query == '.tables':
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        print("📋 Tables:")
                        for table in tables:
                            print(f"   {table[0]}")
                        continue
                    elif query == '.schema':
                        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
                        schemas = cursor.fetchall()
                        print("📋 All Schemas:")
                        for schema in schemas:
                            if schema[0]:
                                print(f"   {schema[0]};")
                        continue
                    elif query.startswith('.schema '):
                        table_name = query.split(' ', 1)[1]
                        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
                        schema = cursor.fetchone()
                        if schema:
                            print(f"📋 Schema for {table_name}:")
                            print(f"   {schema[0]};")
                        else:
                            print(f"❌ Table '{table_name}' not found")
                        continue
                    else:
                        print(f"❌ Unknown command: {query}")
                        continue
                
                # Handle SQL commands
                if query.upper().startswith('SELECT') or query.upper().startswith('PRAGMA'):
                    cursor.execute(query)
                    results = cursor.fetchall()
                    
                    if results:
                        # Get column names
                        col_names = [description[0] for description in cursor.description]
                        
                        # Print header
                        header = " | ".join([name.ljust(15) for name in col_names])
                        print(header)
                        print("-" * len(header))
                        
                        # Print results
                        for row in results:
                            row_data = []
                            for value in row:
                                if value is None:
                                    display_value = "NULL"
                                elif isinstance(value, str) and len(value) > 15:
                                    display_value = value[:12] + "..."
                                else:
                                    display_value = str(value)
                                row_data.append(display_value.ljust(15))
                            print(" | ".join(row_data))
                        
                        print(f"\n📊 {len(results)} row(s) returned")
                    else:
                        print("📊 No results returned")
                        
                elif query.upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    cursor.execute(query)
                    conn.commit()
                    print(f"✅ Query executed successfully. {cursor.rowcount} row(s) affected.")
                    
                else:
                    # Try to execute any other SQL command
                    cursor.execute(query)
                    conn.commit()
                    print("✅ Query executed successfully.")
                    
            except sqlite3.Error as e:
                print(f"❌ SQL Error: {e}")
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        conn.close()
        print("👋 Goodbye!")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_file = sys.argv[1]
    else:
        print("Available databases:")
        print("1. users.db (User management, chat sessions, messages)")
        print("2. feedback.db (Legacy feedback system)")
        db_file = input("Enter database file (default: users.db): ").strip() or "users.db"
    
    interactive_shell(db_file)