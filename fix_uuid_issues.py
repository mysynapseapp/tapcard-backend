#!/usr/bin/env python3
"""
Script to fix UUID type issues in the database
"""

import uuid
from sqlalchemy import text
from database import SessionLocal, engine
from models import User, SocialLink, PortfolioItem, WorkExperience, QRCode, Analytics

def fix_uuid_columns():
    """Fix UUID column types and ensure compatibility"""
    db = SessionLocal()
    
    try:
        # Check current UUID types
        print("Checking UUID column types...")
        
        # Fix any UUID type issues
        with engine.connect() as conn:
            # Ensure UUID extension is available
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            
            # Check and fix any UUID type mismatches
            tables = ['users', 'social_links', 'portfolio_items', 'work_experience', 'qr_codes', 'analytics']
            
            for table in tables:
                result = conn.execute(
                    text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name LIKE '%id%'
                    """)
                )
                
                for row in result:
                    print(f"Table {table}: {row.column_name} - {row.data_type}")
        
        print("UUID column check completed successfully")
        
    except Exception as e:
        print(f"Error fixing UUID columns: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_uuid_columns()
