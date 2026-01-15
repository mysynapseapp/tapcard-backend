"""
PostgreSQL migration script to add is_profile_complete column to users table.

Run this script to update the database schema:
    cd tapcard-backend
    source venv/bin/activate
    python migrations/migrate_pg_is_profile_complete.py
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text

def migrate():
    """Add is_profile_complete column to users table for PostgreSQL."""
    
    print("🔄 Connecting to database...")
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_profile_complete'
        """))
        columns = result.fetchall()
        
        if columns:
            print("✅ Column 'is_profile_complete' already exists. Skipping migration.")
            return
        
        # Add the column
        print("🔄 Adding 'is_profile_complete' column to users table...")
        conn.execute(text("""
            ALTER TABLE users ADD COLUMN is_profile_complete BOOLEAN DEFAULT FALSE
        """))
        
        conn.commit()
        
        # Verify the column was added
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_profile_complete'
        """))
        columns = result.fetchall()
        
        if columns:
            print("✅ Migration successful! Column 'is_profile_complete' added.")
        else:
            print("❌ Migration failed. Column not found.")

if __name__ == "__main__":
    migrate()

