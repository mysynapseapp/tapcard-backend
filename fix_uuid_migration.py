#!/usr/bin/env python3
"""
Fix UUID type issues in the database
"""

from sqlalchemy import text
from database import engine

def fix_uuid_types():
    """Fix UUID type mismatches in the database"""
    
    print("Starting UUID type migration...")
    
    with engine.connect() as conn:
        # Fix social_links.user_id
        print("Checking social_links.user_id...")
        result = conn.execute(text("""
            SELECT data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'social_links' AND column_name = 'user_id'
        """))
        
        row = result.fetchone()
        if row and row.udt_name == 'varchar':
            print("  Converting social_links.user_id from VARCHAR to UUID...")
            
            # Drop foreign key constraint
            conn.execute(text("""
                ALTER TABLE social_links 
                DROP CONSTRAINT IF EXISTS social_links_user_id_fkey
            """))
            
            # Alter column type
            conn.execute(text("""
                ALTER TABLE social_links 
                ALTER COLUMN user_id TYPE UUID USING user_id::UUID
            """))
            
            # Add foreign key constraint
            conn.execute(text("""
                ALTER TABLE social_links 
                ADD CONSTRAINT social_links_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(id)
            """))
            
            print("  ✓ Fixed social_links.user_id")
        
        # Fix other tables
        tables = [
            ('portfolio_items', 'user_id'),
            ('work_experience', 'user_id'),
            ('qr_codes', 'user_id'),
            ('analytics', 'user_id')
        ]
        
        for table, column in tables:
            print(f"Checking {table}.{column}...")
            result = conn.execute(text(f"""
                SELECT data_type, udt_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{column}'
            """))
            
            row = result.fetchone()
            if row and row.udt_name == 'varchar':
                print(f"  Converting {table}.{column} from VARCHAR to UUID...")
                
                # Drop foreign key constraint
                conn.execute(text(f"""
                    ALTER TABLE {table} 
                    DROP CONSTRAINT IF EXISTS {table}_{column}_fkey
                """))
                
                # Alter column type
                conn.execute(text(f"""
                    ALTER TABLE {table} 
                    ALTER COLUMN {column} TYPE UUID USING {column}::UUID
                """))
                
                # Add foreign key constraint
                conn.execute(text(f"""
                    ALTER TABLE {table} 
                    ADD CONSTRAINT {table}_{column}_fkey 
                    FOREIGN KEY ({column}) REFERENCES users(id)
                """))
                
                print(f"  ✓ Fixed {table}.{column}")
            else:
                print(f"  ✓ {table}.{column} is already UUID type")
        
        print("All UUID type fixes completed!")

if __name__ == "__main__":
    fix_uuid_types()
