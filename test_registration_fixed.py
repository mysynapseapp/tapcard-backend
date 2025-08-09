#!/usr/bin/env python3
"""
Fixed test script for registration testing
Uses unique email addresses to avoid conflicts
"""

import requests
import json
import sys
import os
import random
import string

API_BASE_URL = "http://localhost:8000/api"

def generate_unique_email():
    """Generate a unique email address for testing"""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_suffix}@example.com"

def generate_unique_username():
    """Generate a unique username for testing"""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"testuser_{random_suffix}"

def test_registration():
    """Test registration endpoint with unique data"""
    
    print("=" * 60)
    print("REGISTRATION TEST (FIXED)")
    print("=" * 60)
    
    # Generate unique test data
    test_data = {
        "username": generate_unique_username(),
        "email": generate_unique_email(),
        "password": "testpass123"
    }
    
    print(f"Testing with:")
    print(f"Username: {test_data['username']}")
    print(f"Email: {test_data['email']}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Registration successful!")
            print("Response:", json.dumps(response.json(), indent=2))
            return True
        elif response.status_code == 400:
            print("❌ Validation error:", response.json())
            return False
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print("Response:", response.text)
            return False
            
    except Exception as e:
        print("❌ Error:", str(e))
        return False

if __name__ == "__main__":
    test_registration()
