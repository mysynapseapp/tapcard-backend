#!/usr/bin/env python3
"""
Script to add the missing fullname column to the users table
"""

import os
import sys
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def add_fullname_column():
    """Add the fullname column to the users table"""
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.begin() as connection:
            # Check if fullname column exists
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'fullname'
            """))
            
            if result.fetchone():
                print("fullname column already exists")
                return
            
            # Add the fullname column
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN fullname VARCHAR(255) NOT NULL DEFAULT 'User'
            """))
            
            print("Successfully added fullname column to users table")
            
    except Exception as e:
        print(f"Error adding fullname column: {e}")
        raise

if __name__ == "__main__":
    add_fullname_column()
