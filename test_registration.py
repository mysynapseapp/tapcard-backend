#!/usr/bin/env python3
"""
Test script to diagnose registration issues
This script will test the registration endpoint directly and capture detailed errors
"""

import requests
import json
import sys
import os

# Test configuration
API_BASE_URL = "http://localhost:8000/api"
# For local testing, use: API_BASE_URL = "http://localhost:8000/api"

def test_registration():
    """Test registration endpoint with detailed error reporting"""
    
    print("🧪 Testing registration endpoint...")
    print(f"API URL: {API_BASE_URL}")
    
    # Test data
    test_data = {
        "username": "testuser123",
        "email": "test123@example.com",
        "password": "testpass123"
    }
    
    try:
        print("\n📤 Sending registration request...")
        print("Payload:", json.dumps(test_data, indent=2))
        
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Registration successful!")
            print("Response:", json.dumps(response.json(), indent=2))
            return True
        elif response.status_code == 400:
            print("❌ Validation error:")
            print("Response:", json.dumps(response.json(), indent=2))
            return False
        elif response.status_code == 500:
            print("❌ Server error:")
            try:
                error_data = response.json()
                print("Error response:", json.dumps(error_data, indent=2))
            except:
                print("Raw error response:", response.text)
            return False
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print("Response:", response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - backend may be down")
        return False
    except requests.exceptions.ConnectionError as e:
        print("❌ Connection error:", str(e))
        return False
    except Exception as e:
        print("❌ Unexpected error:", str(e))
        return False

def test_health_check():
    """Test if the backend is accessible"""
    
    try:
        print("\n🔍 Testing backend health...")
        response = requests.get("https://tapcard-backend.onrender.com", timeout=5)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backend is accessible")
            return True
        else:
            print("❌ Backend health check failed")
            return False
    except Exception as e:
        print("❌ Backend not accessible:", str(e))
        return False

def test_login():
    """Test login endpoint with existing credentials"""
    
    login_data = {
        "username": "test123@example.com",
        "password": "testpass123"
    }
    
    try:
        print("\n🔐 Testing login endpoint...")
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print(f"Login status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Login successful!")
            return True
        else:
            print("❌ Login failed:", response.text)
            return False
            
    except Exception as e:
        print("❌ Login test error:", str(e))
        return False

def main():
    """Run comprehensive registration tests"""
    
    print("=" * 60)
    print("REGISTRATION DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Test backend accessibility
    if not test_health_check():
        print("\n❌ Backend is not accessible. Please check if the server is running.")
        return
    
    # Test registration
    registration_success = test_registration()
    
    # Test login (if registration fails)
    if not registration_success:
        print("\n" + "=" * 60)
        print("ADDITIONAL TESTS")
        print("=" * 60)
        test_login()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if registration_success:
        print("✅ Registration is working correctly")
    else:
        print("❌ Registration is failing - check the error details above")
        print("\nNext steps:")
        print("1. Check backend logs for detailed error messages")
        print("2. Verify database connection")
        print("3. Check if all required fields are being sent")

if __name__ == "__main__":
    main()
