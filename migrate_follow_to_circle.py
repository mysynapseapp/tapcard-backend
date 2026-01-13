"""
Database Migration: Follow Model → Circle Model

This script migrates the database from the old Follow model to the new Circle model.
The Circle model uses a LinkedIn-style mutual relationship with pending/accepted states.

Changes:
1. Rename table: follows → circles
2. Rename columns: follower_id → requester_id, following_id → receiver_id
3. Add status column with default 'pending' for existing records
4. Add created_at column if not exists

Run this script with: python migrate_db.py
"""

import sqlite3
import os

# Get the database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'tapcard.db')

def migrate():
    """Run the migration"""
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if old 'follows' table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='follows'")
    follows_exists = cursor.fetchone() is not None
    
    # Check if new 'circles' table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='circles'")
    circles_exists = cursor.fetchone() is not None
    
    if circles_exists:
        print("✓ 'circles' table already exists. Migration may have already been run.")
        conn.close()
        return
    
    if not follows_exists:
        print("✗ 'follows' table does not exist. Creating 'circles' table from scratch...")
        # Create the circles table directly
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS circles (
                id TEXT PRIMARY KEY,
                requester_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (requester_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        print("✓ Created 'circles' table")
        conn.close()
        return
    
    # Migration steps for existing 'follows' table
    print("Starting migration from 'follows' to 'circles'...")
    
    # Step 1: Create the new circles table with all columns
    print("Step 1: Creating new 'circles' table...")
    cursor.execute('''
        CREATE TABLE circles (
            id TEXT PRIMARY KEY,
            requester_id TEXT NOT NULL,
            receiver_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (requester_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    ''')
    
    # Step 2: Copy data from follows to circles, converting the relationship
    # In Follow model: follower_id follows following_id
    # In Circle model: We need to convert to a mutual relationship
    # For existing follows, we'll set status to 'accepted' since they were already connected
    print("Step 2: Copying data from 'follows' to 'circles'...")
    cursor.execute('''
        INSERT INTO circles (id, requester_id, receiver_id, status, created_at)
        SELECT 
            id,
            follower_id AS requester_id,
            following_id AS receiver_id,
            'accepted' AS status,
            COALESCE(created_at, datetime('now')) AS created_at
        FROM follows
    ''')
    
    # Step 3: Drop the old follows table
    print("Step 3: Dropping old 'follows' table...")
    cursor.execute('DROP TABLE follows')
    
    # Step 4: Create index on requester_id and receiver_id
    print("Step 4: Creating indexes...")
    cursor.execute('CREATE INDEX idx_circles_requester ON circles(requester_id)')
    cursor.execute('CREATE INDEX idx_circles_receiver ON circles(receiver_id)')
    cursor.execute('CREATE INDEX idx_circles_status ON circles(status)')
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("✓ Migration completed successfully!")
    print("")
    print("Summary:")
    print("  - 'follows' table has been replaced with 'circles'")
    print("  - Column 'follower_id' renamed to 'requester_id'")
    print("  - Column 'following_id' renamed to 'receiver_id'")
    print("  - Added 'status' column (existing follows set to 'accepted')")
    print("  - Added 'created_at' column if not present")

if __name__ == "__main__":
    migrate()

