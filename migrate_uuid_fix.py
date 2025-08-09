#!/usr/bin/env python3
"""
Migration script to fix UUID type issues in the production database
This script will update the database schema to use proper UUID types
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, inspect
from database import Base, engine

def migrate_database():
    """Migrate production database to fix UUID issues"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    if not database_url.startswith("postgresql"):
        print("⚠️  Not using PostgreSQL, skipping UUID migration")
        return True
    
    try:
        print("🔧 Starting UUID type migration...")
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check current database state
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'social_links', 'portfolio_items', 'work_experience', 'qr_codes', 'analytics')
        """)
        
        tables = cursor.fetchall()
        if not tables:
            print("📋 No existing tables found, creating new ones...")
            Base.metadata.create_all(bind=engine)
            print("✅ Tables created successfully")
            return True
        
        # Check if migration is needed
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'id'
        """)
        
        result = cursor.fetchone()
        if result and result[1] == 'uuid':
            print("✅ Database already uses UUID types, skipping migration")
            return True
        
        print("🔄 Migrating database schema to UUID types...")
        
        # Drop all tables and recreate with proper UUID types
        print("🗑️  Dropping existing tables...")
        cursor.execute("DROP TABLE IF EXISTS analytics CASCADE")
        cursor.execute("DROP TABLE IF EXISTS qr_codes CASCADE")
        cursor.execute("DROP TABLE IF EXISTS work_experience CASCADE")
        cursor.execute("DROP TABLE IF EXISTS portfolio_items CASCADE")
        cursor.execute("DROP TABLE IF EXISTS social_links CASCADE")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        
        print("📊 Creating new tables with UUID types...")
        Base.metadata.create_all(bind=engine)
        
        cursor.close()
        conn.close()
        
        print("✅ Database migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def check_database_schema():
    """Check current database schema"""
    
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("📋 Current database tables:")
        for table in tables:
            columns = inspector.get_columns(table)
            print(f"\n{table}:")
            for col in columns:
                print(f"  {col['name']}: {col['type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking schema: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database migration...")
    
    # Check current schema
    check_database_schema()
    
    # Run migration
    success = migrate_database()
    
    if success:
        print("✅ Migration completed successfully!")
        print("🔄 Please restart your backend server to apply changes")
    else:
        print("❌ Migration failed - please check the error messages above")
        sys.exit(1)
