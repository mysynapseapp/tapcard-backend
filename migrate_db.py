#!/usr/bin/env python3
"""
Database migration script for Neon DB (PostgreSQL)
This script safely migrates your existing database to the new schema using SQLAlchemy
"""

import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Import your models
from models import User, Base, PasskeyCredential
from database import DATABASE_URL

load_dotenv()

def generate_uuid():
    return str(uuid.uuid4())

def migrate_database():
    """Migrate the database to match the new User model using SQLAlchemy"""
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create inspector to check current schema
        inspector = inspect(engine)
        
        # Check if users table exists
        if 'users' not in inspector.get_table_names():
            print("Users table does not exist. Creating new table...")
            Base.metadata.create_all(engine)
            print("Database schema created successfully!")
            return
        
        # Get current table info
        current_columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"Current columns: {current_columns}")
        
        # Check if migration is needed - specifically check for firebase_uid column
        required_columns = ['username', 'email', 'password_hash', 'firebase_uid']
        missing_columns = [col for col in required_columns if col not in current_columns]
        
        if not missing_columns:
            print("Database schema is already up to date!")
            return
        
        print(f"Migration needed. Missing columns: {missing_columns}")
        
        print(f"Missing columns: {missing_columns}")
        
        # Start transaction
        with engine.begin() as connection:
            # Create new table with updated schema
            new_table_name = 'users_new'
            
            # Drop new table if it exists from previous failed migration
            connection.execute(text(f"DROP TABLE IF EXISTS {new_table_name}"))
            
            # Create new table with correct schema
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS users_new (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    fullname VARCHAR(255) NOT NULL,
                    bio TEXT,
                    dob DATE,
                    firebase_uid VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            connection.execute(text(create_table_sql))
            
            # Check if old users table exists and has data
            result = connection.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            if user_count > 0:
                print(f"Found {user_count} existing users to migrate")
                
                # Get data from old table
                result = connection.execute(text("SELECT * FROM users"))
                old_users = result.fetchall()
                
                # Migrate each user
                for user in old_users:
                    user_dict = dict(user._mapping)
                    
                    # Generate new user data
                    new_id = user_dict.get('id', generate_uuid())
                    username = user_dict.get('username', f"user_{str(new_id)[:8]}")
                    email = user_dict.get('email', f"{username}@example.com")
                    password_hash = user_dict.get('password_hash', 'placeholder_hash')
                    fullname = user_dict.get('fullname', username)  # Use username as fallback
                    bio = user_dict.get('bio')
                    dob = user_dict.get('dob')
                    created_at = user_dict.get('created_at', datetime.utcnow())
                    updated_at = user_dict.get('updated_at', datetime.utcnow())
                    
                    # Insert into new table
                    insert_sql = """
                        INSERT INTO users_new (id, username, email, password_hash, fullname, bio, dob, firebase_uid, created_at, updated_at)
                        VALUES (:id, :username, :email, :password_hash, :fullname, :bio, :dob, :firebase_uid, :created_at, :updated_at)
                    """
                    connection.execute(text(insert_sql), {
                        'id': new_id,
                        'username': username,
                        'email': email,
                        'password_hash': password_hash,
                        'fullname': fullname,
                        'bio': bio,
                        'dob': dob,
                        'firebase_uid': None,  # Set to None for existing users
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
                
                print("Data migration completed")
            
            # Rename old table as backup with timestamp to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_table_name = f"users_backup_{timestamp}"
            connection.execute(text(f"ALTER TABLE users RENAME TO {backup_table_name}"))
            print(f"Old users table renamed to {backup_table_name}")
            
            # Rename new table to users
            connection.execute(text(f"ALTER TABLE {new_table_name} RENAME TO users"))
            
            # Create indexes for better performance
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
            
            print("Database migration completed successfully!")
            
            # Verify new schema
            inspector = inspect(engine)
            new_columns = [col['name'] for col in inspector.get_columns('users')]
            print(f"New columns: {new_columns}")
            
    except SQLAlchemyError as e:
        print(f"Error during migration: {e}")
        session.rollback()
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def check_database_schema():
    """Check current database schema without making changes"""
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("=== Database Schema Check ===")
    
    # List all tables
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    
    if 'users' in tables:
        # Get users table info
        columns = inspector.get_columns('users')
        print("\nUsers table columns:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # Get indexes
        indexes = inspector.get_indexes('users')
        if indexes:
            print("\nUsers table indexes:")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")
    
    engine.dispose()

def reset_database():
    """Reset database - WARNING: This will delete all data!"""
    
    confirm = input("Are you sure you want to reset the database? This will delete ALL data! (yes/no): ")
    if confirm.lower() != 'yes':
        print("Database reset cancelled")
        return
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.begin() as connection:
            # Drop existing tables
            connection.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS social_links CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS portfolio_items CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS work_experience CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS qr_codes CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS analytics CASCADE"))
            
            # Create all tables with current schema
            Base.metadata.create_all(engine)
            print("Database reset completed successfully!")
            
    except Exception as e:
        print(f"Error resetting database: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'check':
            check_database_schema()
        elif command == 'reset':
            reset_database()
        else:
            print("Usage: python migrate_db.py [check|reset]")
            print("  check - Check current database schema")
            print("  reset - Reset database (WARNING: deletes all data)")
    else:
        migrate_database()
