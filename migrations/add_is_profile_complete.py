"""
Database migration script to add is_profile_complete column to users table.

Run this script to update the database schema:
    python migrations/add_is_profile_complete.py

Or run the SQL directly:
    ALTER TABLE users ADD COLUMN is_profile_complete BOOLEAN DEFAULT FALSE;
"""

import sqlite3
import os

def migrate():
    """Add is_profile_complete column to users table."""
    
    # Path to the database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'tapcard.db')
    db_path = os.path.abspath(db_path)
    
    print(f"🔄 Connecting to database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_profile_complete' in columns:
        print("✅ Column 'is_profile_complete' already exists. Skipping migration.")
        conn.close()
        return
    
    # Add the column
    print("🔄 Adding 'is_profile_complete' column to users table...")
    cursor.execute("""
        ALTER TABLE users ADD COLUMN is_profile_complete BOOLEAN DEFAULT FALSE
    """)
    
    conn.commit()
    
    # Verify the column was added
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_profile_complete' in columns:
        print("✅ Migration successful! Column 'is_profile_complete' added.")
    else:
        print("❌ Migration failed. Column not found.")
    
    conn.close()

if __name__ == "__main__":
    migrate()

