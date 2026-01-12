# migrate_passkeys.py
#!/usr/bin/env python3
"""
Script to create the passkey_credentials table
"""

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import PasskeyCredential
from database import DATABASE_URL

def create_passkeys_table():
    print("🚀 Starting passkey credentials migration...")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        inspector = inspect(engine)
        
        # Check if passkey_credentials table exists
        if 'passkey_credentials' not in inspector.get_table_names():
            print("🔄 Creating passkey_credentials table...")
            PasskeyCredential.__table__.create(engine)
            print("✅ Created passkey_credentials table")
        else:
            print("✅ passkey_credentials table already exists")
            
        print("✨ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    create_passkeys_table()