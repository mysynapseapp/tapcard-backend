from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE users DROP COLUMN IF EXISTS firebase_uid'))
    conn.commit()
    print("firebase_uid column dropped if it existed")
