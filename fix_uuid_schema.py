#!/usr/bin/env python3
"""
Fix for social_links UUID type mismatch issue
This script updates the id column from VARCHAR to UUID
"""

import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import SessionLocal, engine

def fix_uuid_schema():
    """Fix the social_links table schema to use UUID for id column"""
    
    print("🔧 Fixing social_links UUID schema...")
    
    with SessionLocal() as db:
        try:
            # Step 1: Create a new table with correct UUID types
            print("📋 Creating new table with correct UUID types...")
            db.execute(text("""
                CREATE TABLE social_links_new (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    platform_name VARCHAR NOT NULL,
                    link_url VARCHAR NOT NULL
                );
            """))
            
            # Step 2: Copy existing data to new table
            print("📊 Migrating existing data...")
            db.execute(text("""
                INSERT INTO social_links_new (id, user_id, platform_name, link_url)
                SELECT 
                    CASE 
                        WHEN id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                        THEN id::uuid
                        ELSE gen_random_uuid()
                    END,
                    user_id,
                    platform_name,
                    link_url
                FROM social_links;
            """))
            
            # Step 3: Drop old table and rename new table
            print("🔄 Replacing old table with new one...")
            db.execute(text("DROP TABLE social_links;"))
            db.execute(text("ALTER TABLE social_links_new RENAME TO social_links;"))
            
            # Step 4: Create indexes for better performance
            print("📈 Creating indexes...")
            db.execute(text("""
                CREATE INDEX idx_social_links_user_id ON social_links(user_id);
                CREATE INDEX idx_social_links_id ON social_links(id);
            """))
            
            db.commit()
            print("✅ Successfully fixed social_links UUID schema")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    print("🚀 Starting UUID schema fix...")
    
    try:
        fix_uuid_schema()
        print("🎉 Schema fix completed successfully!")
        
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)
