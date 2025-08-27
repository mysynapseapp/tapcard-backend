#!/usr/bin/env python3
"""
Simple test script to verify registration endpoint
"""

import requests
import json
import random

BASE_URL = "http://localhost:8000/api/auth"
HEADERS = {"Content-Type": "application/json"}

def test_registration():
    """Test user registration endpoint"""
    
    username = f"testuser_{random.randint(10000, 99999)}"
    email = f"{username}@example.com"
    password = "TestPass123!"
    fullname = f"Test User {random.randint(100, 999)}"
    
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "fullname": fullname
    }
    
    print(f"Testing registration for: {username}")
    print(f"Email: {email}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            headers=HEADERS,
            json=user_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Registration successful!")
            return True
        else:
            print("❌ Registration failed!")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

if __name__ == "__main__":
    print("Testing registration endpoint...")
    success = test_registration()
    
    if success:
        print("\n🎉 Registration endpoint is working correctly!")
    else:
        print("\n❌ Registration endpoint needs investigation!")
