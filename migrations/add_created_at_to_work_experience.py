from sqlalchemy import text
from database import engine

def upgrade():
    # Add created_at column if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE work_experience 
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        """))
        conn.commit()

if __name__ == "__main__":
    upgrade()
