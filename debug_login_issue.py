#!/usr/bin/env python3
"""
Debug script for login issue with curltest@example.com
"""
import requests
import json
import sys
import os

# Use the production URL
API_BASE_URL = "https://tapcard-backend.onrender.com/api"

def test_user_exists():
    """Check if the user exists in the database"""
    print("🔍 Checking if user exists...")
    
    # Try to register the user first to ensure they exist
    register_data = {
        "username": "curltest",
        "email": "curltest@example.com",
        "password": "curltest123"
    }
    
    try:
        # Try to register the user
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ User registered successfully")
            return True
        elif response.status_code == 400:
            error = response.json()
            if "Email already registered" in str(error):
                print("✅ User already exists in database")
                return True
            else:
                print(f"❌ Registration error: {error}")
                return False
        else:
            print(f"❌ Unexpected registration response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking user existence: {e}")
        return False

def test_login_with_variations():
    """Test login with different variations"""
    print("\n🔐 Testing login with different approaches...")
    
    # Test 1: Standard login with form data
    login_data_form = {
        "username": "curltest@example.com",
        "password": "curltest123"
    }
    
    # Test 2: Try with just username (without @example.com)
    login_data_simple = {
        "username": "curltest",
        "password": "curltest123"
    }
    
    # Test 3: Try with URL-encoded email
    login_data_encoded = {
        "username": "curltest%40example.com",
        "password": "curltest123"
    }
    
    test_cases = [
        ("Standard email", login_data_form),
        ("Simple username", login_data_simple),
        ("URL encoded", login_data_encoded)
    ]
    
    for test_name, data in test_cases:
        print(f"\n--- Testing {test_name} ---")
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/login",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Login successful!")
                print("Response:", json.dumps(response.json(), indent=2))
                return True
            else:
                print("❌ Login failed:", response.text)
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_with_json_payload():
    """Test login with JSON payload (for debugging)"""
    print("\n📋 Testing with JSON payload...")
    
    login_json = {
        "email": "curltest@example.com",
        "password": "curltest123"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json=login_json,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"JSON login status: {response.status_code}")
        print("Response:", response.text)
        
    except Exception as e:
        print(f"❌ JSON login error: {e}")

def main():
    """Main debug function"""
    print("=" * 60)
    print("LOGIN ISSUE DEBUGGER")
    print("=" * 60)
    print("Testing credentials: curltest@example.com / curltest123")
    print("API URL:", API_BASE_URL)
    
    # First ensure user exists
    user_exists = test_user_exists()
    
    if user_exists:
        print("\n✅ User confirmed to exist")
        
        # Test different login approaches
        login_success = test_login_with_variations()
        
        if not login_success:
            print("\n🔍 Trying JSON payload approach...")
            test_with_json_payload()
    else:
        print("\n❌ User does not exist or registration failed")
    
    print("\n" + "=" * 60)
    print("DEBUG SUMMARY")
    print("=" * 60)
    print("If login is still failing, possible causes:")
    print("1. Password hash mismatch in database")
    print("2. Email case sensitivity issue")
    print("3. Database connection issue")
    print("4. Backend authentication logic error")

if __name__ == "__main__":
    main()
