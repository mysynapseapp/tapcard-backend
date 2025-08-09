"""
Fix for UUID type mismatch in social_links table
This script fixes the error:
"operator does not exist: character varying = uuid"
by ensuring the user_id column in social_links is properly UUID type
"""

import uuid
from sqlalchemy import text
from database import SessionLocal, engine
from models import Base, SocialLink

def fix_social_links_uuid_type():
    """Fix the UUID type mismatch in social_links table"""
    print("Starting UUID type fix for social_links table...")
    
    with SessionLocal() as db:
        try:
            # Check current column type
            result = db.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'social_links' 
                AND column_name = 'user_id';
            """))
            current_type = result.scalar()
            print(f"Current user_id column type: {current_type}")
            
            if current_type and current_type.lower() != 'uuid':
                print("Converting user_id column from VARCHAR to UUID...")
                
                # Step 1: Add a new UUID column
                db.execute(text("""
                    ALTER TABLE social_links 
                    ADD COLUMN user_id_uuid UUID;
                """))
                
                # Step 2: Migrate data from old column to new UUID column
                db.execute(text("""
                    UPDATE social_links 
                    SET user_id_uuid = user_id::UUID;
                """))
                
                # Step 3: Drop foreign key constraints temporarily
                db.execute(text("""
                    ALTER TABLE social_links 
                    DROP CONSTRAINT IF EXISTS social_links_user_id_fkey;
                """))
                
                # Step 4: Drop old column and rename new one
                db.execute(text("""
                    ALTER TABLE social_links 
                    DROP COLUMN user_id;
                """))
                
                db.execute(text("""
                    ALTER TABLE social_links 
                    RENAME COLUMN user_id_uuid TO user_id;
                """))
                
                # Step 5: Recreate foreign key constraint
                db.execute(text("""
                    ALTER TABLE social_links 
                    ADD CONSTRAINT social_links_user_id_fkey 
                    FOREIGN KEY (user_id) REFERENCES users(id);
                """))
                
                print("Successfully converted user_id column to UUID type")
            else:
                print("user_id column is already UUID type")
                
            # Verify the fix
            result = db.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'social_links' 
                AND column_name = 'user_id';
            """))
            final_type = result.scalar()
            print(f"Final user_id column type: {final_type}")
            
            db.commit()
            print("UUID type fix completed successfully")
            
        except Exception as e:
            db.rollback()
            print(f"Error during UUID type fix: {str(e)}")
            raise

def verify_fix():
    """Verify the fix works by testing a sample query"""
    print("Verifying the fix...")
    
    with SessionLocal() as db:
        try:
            # Test the query that's failing
            test_user_id = "35b2aea2-4251-4d29-b7e5-d3b1a70573b6"
            result = db.execute(
                text("SELECT * FROM social_links WHERE user_id = :user_id"),
                {"user_id": test_user_id}
            )
            print("Query executed successfully - fix verified!")
            return True
        except Exception as e:
            print(f"Verification failed: {str(e)}")
            return False

if __name__ == "__main__":
    fix_social_links_uuid_type()
    verify_fix()
