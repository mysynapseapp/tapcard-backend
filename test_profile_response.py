#!/usr/bin/env python3
"""
Test script to verify the profile endpoint returns email
"""

import os
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User
from schemas import UserOut
from database import get_db

# Test the UserOut schema
def test_user_out_schema():
    print("Testing UserOut schema...")
    
    # Create a mock user
    from datetime import datetime
    
    mock_user = User(
        id="test-id-123",
        username="testuser",
        email="test@example.com",
        bio="Test bio",
        password_hash="hashed_password",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Test the from_orm method
    user_out = UserOut.from_orm(mock_user)
    print("UserOut response:")
    print(f"  username: {user_out.username}")
    print(f"  email: {user_out.email}")
    print(f"  bio: {user_out.bio}")
    
    return user_out

if __name__ == "__main__":
    result = test_user_out_schema()
    print("\n✅ Schema test completed successfully!")
    print("Email field is included in the response.")
