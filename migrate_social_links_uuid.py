"""
Migration script to fix UUID type mismatch in social_links table
Run this script to migrate the database schema
"""

import os
import sys
from sqlalchemy import text
from database import SessionLocal

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrate_social_links_to_uuid():
    """Migrate social_links table to use UUID type for user_id"""
    
    print("Starting migration of social_links table...")
    
    with SessionLocal() as db:
        try:
            # Check if migration is needed
            result = db.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'social_links' 
                AND column_name = 'user_id';
            """))
            current_type = result.scalar()
            
            if current_type and current_type.lower() == 'uuid':
                print("social_links.user_id is already UUID type - no migration needed")
                return
            
            print(f"Current type: {current_type}, migrating to UUID...")
            
            # Step 1: Create new UUID column
            db.execute(text("""
                ALTER TABLE social_links 
                ADD COLUMN user_id_uuid UUID;
            """))
            
            # Step 2: Migrate data
            db.execute(text("""
                UPDATE social_links 
                SET user_id_uuid = user_id::UUID;
            """))
            
            # Step 3: Drop old column and rename new one
            db.execute(text("""
                ALTER TABLE social_links 
                DROP COLUMN user_id;
            """))
            
            db.execute(text("""
                ALTER TABLE social_links 
                RENAME COLUMN user_id_uuid TO user_id;
            """))
            
            # Step 4: Add foreign key constraint
            db.execute(text("""
                ALTER TABLE social_links 
                ADD CONSTRAINT social_links_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(id);
            """))
            
            # Step 5: Create index for performance
            db.execute(text("""
                CREATE INDEX idx_social_links_user_id ON social_links(user_id);
            """))
            
            db.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            db.rollback()
            print(f"Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_social_links_to_uuid()
