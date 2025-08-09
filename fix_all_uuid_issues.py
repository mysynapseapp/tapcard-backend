"""
Comprehensive fix for all UUID type mismatches in the database
This script fixes UUID type issues across all tables
"""

import uuid
from sqlalchemy import text
from database import SessionLocal, engine

def fix_analytics_uuid_type():
    """Fix the UUID type mismatch in analytics table"""
    print("Starting UUID type fix for analytics table...")
    
    with SessionLocal() as db:
        try:
            # Check current column type
            result = db.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'analytics' 
                AND column_name = 'user_id';
            """))
            current_type = result.scalar()
            print(f"Current user_id column type: {current_type}")
            
            if current_type and current_type.lower() != 'uuid':
                print("Converting user_id column from VARCHAR to UUID...")
                
                # Step 1: Add a new UUID column
                db.execute(text("""
                    ALTER TABLE analytics 
                    ADD COLUMN user_id_uuid UUID;
                """))
                
                # Step 2: Migrate data from old column to new UUID column
                db.execute(text("""
                    UPDATE analytics 
                    SET user_id_uuid = user_id::UUID;
                """))
                
                # Step 3: Drop foreign key constraints temporarily
                db.execute(text("""
                    ALTER TABLE analytics 
                    DROP CONSTRAINT IF EXISTS analytics_user_id_fkey;
                """))
                
                # Step 4: Drop old column and rename new one
                db.execute(text("""
                    ALTER TABLE analytics 
                    DROP COLUMN user_id;
                """))
                
                db.execute(text("""
                    ALTER TABLE analytics 
                    RENAME COLUMN user_id_uuid TO user_id;
                """))
                
                # Step 5: Recreate foreign key constraint
                db.execute(text("""
                    ALTER TABLE analytics 
                    ADD CONSTRAINT analytics_user_id_fkey 
                    FOREIGN KEY (user_id) REFERENCES users(id);
                """))
                
                print("Successfully converted user_id column to UUID type")
            else:
                print("user_id column is already UUID type")
                
            db.commit()
            print("Analytics UUID type fix completed successfully")
            
        except Exception as e:
            db.rollback()
            print(f"Error during analytics UUID type fix: {str(e)}")
            raise

def run_all_fixes():
    """Run all UUID fixes in sequence"""
    print("Starting comprehensive UUID fixes...")
    
    # Import and run individual fixes
    import fix_work_experience_uuid
    import fix_portfolio_uuid
    import fix_qr_code_uuid
    
    # Run each fix
    fix_work_experience_uuid.fix_work_experience_uuid_type()
    fix_portfolio_uuid.fix_portfolio_uuid_type()
    fix_qr_code_uuid.fix_qr_code_uuid_type()
    fix_analytics_uuid_type()
    
    print("All UUID fixes completed successfully!")

if __name__ == "__main__":
    run_all_fixes()
