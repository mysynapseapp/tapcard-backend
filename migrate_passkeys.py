# migrate_passkeys.py
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

def create_passkeys_table():
    print("🚀 Starting passkey credentials migration...")
    
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Dynamically import models to avoid circular imports
        from models import PasskeyCredential, Base
        
        # Create all tables that don't exist
        print("🔄 Checking database schema...")
        Base.metadata.create_all(engine)
        
        # Verify the table was created
        inspector = inspect(engine)
        if 'passkey_credentials' in inspector.get_table_names():
            print("✅ passkey_credentials table is ready")
            return True
        else:
            print("❌ Failed to create passkey_credentials table")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    if create_passkeys_table():
        print("✨ Migration completed successfully!")
    else:
        print("❌ Migration failed")
        exit(1)