import asyncio
from routers.auth import forgot_password
from schemas import ForgotPassword
from database import SessionLocal

async def test_forgot_password():
    email = 'masarukaze041@gmail.com'
    forgot_data = ForgotPassword(email=email)
    
    # Create a database session for the test
    db = SessionLocal()
    try:
        result = await forgot_password(forgot_data, db)
        print(result)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_forgot_password())
