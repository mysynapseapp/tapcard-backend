#!/usr/bin/env python3
"""
Database migration script to update User model schema
This script safely migrates your existing database to the new schema
"""

import sqlite3
import uuid
from datetime import datetime

def migrate_database():
    """Migrate the database to match the new User model"""
    
    # Connect to the database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(users)")
        current_columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {current_columns}")
        
        # Check if migration is needed
        required_columns = ['username', 'email', 'password_hash']
        missing_columns = [col for col in required_columns if col not in current_columns]
        
        if not missing_columns:
            print("Database schema is already up to date!")
            return
        
        print(f"Missing columns: {missing_columns}")
        
        # Create new table with correct schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_new (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                bio TEXT,
                dob DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if old users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            # Get data from old table
            cursor.execute('SELECT * FROM users')
            old_data = cursor.fetchall()
            
            if old_data:
                print(f"Found {len(old_data)} existing users to migrate")
                
                # Get column names from old table
                cursor.execute('PRAGMA table_info(users)')
                old_columns = [row[1] for row in cursor.fetchall()]
                
                # Migrate each user
                for row in old_data:
                    user_dict = dict(zip(old_columns, row))
                    
                    # Generate new user data
                    new_id = user_dict.get('id', str(uuid.uuid4()))
                    username = user_dict.get('username', f"user_{new_id[:8]}")
                    email = f"{username}@example.com"  # Placeholder email
                    password_hash = "placeholder_hash"  # Placeholder password
                    bio = user_dict.get('bio', None)
                    dob = user_dict.get('dob', None)
                    created_at = user_dict.get('created_at', datetime.utcnow())
                    updated_at = user_dict.get('updated_at', datetime.utcnow())
                    
                    cursor.execute('''
                        INSERT INTO users_new (id, username, email, password_hash, bio, dob, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (new_id, username, email, password_hash, bio, dob, created_at, updated_at))
                
                print("Data migration completed")
        
        # Rename old table as backup
        cursor.execute('ALTER TABLE users RENAME TO users_backup')
        
        # Rename new table to users
        cursor.execute('ALTER TABLE users_new RENAME TO users')
        
        # Commit changes
        conn.commit()
        print("Database migration completed successfully!")
        
        # Verify new schema
        cursor.execute("PRAGMA table_info(users)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"New columns: {new_columns}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
