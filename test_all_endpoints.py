#!/usr/bin/env python3
"""
Comprehensive test script for all API endpoints using curltest@example.com / curltest123
"""

import requests
import json
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "curltest@example.com"
TEST_PASSWORD = "curltest123"
TEST_USERNAME = "curltest"
TEST_FULLNAME = "Curl Test User"

# Global variables
token = None
user_id = None
test_user_id = None

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_registration():
    """Test user registration"""
    print_section("1. Testing Registration")
    
    url = f"{BASE_URL}/api/auth/register"
    data = {
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "fullname": TEST_FULLNAME
    }
    
    response = requests.post(url, json=data)
    print_response(response)
    
    if response.status_code == 200:
        global user_id
        user_id = response.json().get("id")
        print(f"✅ Registered user with ID: {user_id}")
    else:
        print("⚠️  Registration failed - user might already exist")
    return response.status_code == 200

def test_login():
    """Test user login"""
    print_section("2. Testing Login")
    
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(url, json=data)
    print_response(response)
    
    if response.status_code == 200:
        global token
        token = response.json().get("access_token")
        print(f"✅ Logged in successfully, token: {token[:20]}...")
    return response.status_code == 200

def test_user_profile():
    """Test getting user profile"""
    print_section("3. Testing User Profile")
    
    if not token:
        print("❌ No token available")
        return False
    
    url = f"{BASE_URL}/api/user/profile"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    print_response(response)
    return response.status_code == 200

def test_search_users():
    """Test searching users"""
    print_section("4. Testing User Search")
    
    if not token:
        print("❌ No token available")
        return False
    
    url = f"{BASE_URL}/api/social/search"
    params = {"username": "test"}
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, params=params, headers=headers)
    print_response(response)
    return response.status_code == 200

def test_follow_unfollow():
    """Test follow/unfollow functionality"""
    print_section("5. Testing Follow/Unfollow")
    
    if not token:
        print("❌ No token available")
        return False
    
    # First, create a test user to follow
    test_user_data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "testpass123",
        "fullname": "Test User"
    }
    
    # Register test user
    register_url = f"{BASE_URL}/api/auth/register"
    register_response = requests.post(register_url, json=test_user_data)
    
    if register_response.status_code == 200:
        test_user_id = register_response.json().get("id")
        print(f"✅ Created test user with ID: {test_user_id}")
        
        # Test follow
        follow_url = f"{BASE_URL}/api/social/follow/{test_user_id}"
        follow_response = requests.post(follow_url, headers={"Authorization": f"Bearer {token}"})
        print("Follow Response:")
        print_response(follow_response)
        
        # Test get followers
        followers_url = f"{BASE_URL}/api/social/followers/{test_user_id}"
        followers_response = requests.get(followers_url, headers={"Authorization": f"Bearer {token}"})
        print("Followers Response:")
        print_response(followers_response)
        
        # Test get following
        following_url = f"{BASE_URL}/api/social/following/{user_id}"
        following_response = requests.get(following_url, headers={"Authorization": f"Bearer {token}"})
        print("Following Response:")
        print_response(following_response)
        
        # Test unfollow
        unfollow_url = f"{BASE_URL}/api/social/unfollow/{test_user_id}"
        unfollow_response = requests.delete(unfollow_url, headers={"Authorization": f"Bearer {token}"})
        print("Unfollow Response:")
        print_response(unfollow_response)
        
        return True
    else:
        print("❌ Failed to create test user")
        return False

def test_social_links():
    """Test social links endpoints"""
    print_section("6. Testing Social Links")
    
    if not token:
        print("❌ No token available")
        return False
    
    # Test add social link
    url = f"{BASE_URL}/api/user/social-links"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "platform_name": "LinkedIn",
        "link_url": "https://linkedin.com/in/curltest"
    }
    
    response = requests.post(url, json=data, headers=headers)
    print_response(response)
    return response.status_code == 200

def test_portfolio():
    """Test portfolio endpoints"""
    print_section("7. Testing Portfolio")
    
    if not token:
        print("❌ No token available")
        return False
    
    url = f"{BASE_URL}/api/user/portfolio"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": "Test Project",
        "description": "A test portfolio item",
        "media_url": "https://example.com/test.jpg"
    }
    
    response = requests.post(url, json=data, headers=headers)
    print_response(response)
    return response.status_code == 200

def test_work_experience():
    """Test work experience endpoints"""
    print_section("8. Testing Work Experience")
    
    if not token:
        print("❌ No token available")
        return False
    
    url = f"{BASE_URL}/api/user/work-experience"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "company_name": "Test Company",
        "role": "Software Engineer",
        "start_date": "2023-01-01",
        "description": "Test work experience"
    }
    
    response = requests.post(url, json=data, headers=headers)
    print_response(response)
    return response.status_code == 200

def test_qr_code():
    """Test QR code endpoints"""
    print_section("9. Testing QR Code")
    
    if not token:
        print("❌ No token available")
        return False
    
    url = f"{BASE_URL}/api/user/qr-code"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    print_response(response)
    return response.status_code == 200

def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 Starting comprehensive API endpoint testing...")
    print(f"Using credentials: {TEST_EMAIL} / {TEST_PASSWORD}")
    
    results = []
    
    # Test registration and login
    reg_success = test_registration()
    login_success = test_login()
    
    if login_success:
        # Test all authenticated endpoints
        results.append(test_user_profile())
        results.append(test_search_users())
        results.append(test_follow_unfollow())
        results.append(test_social_links())
        results.append(test_portfolio())
        results.append(test_work_experience())
        results.append(test_qr_code())
    
    print_section("Test Summary")
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests completed successfully!")
    else:
        print("⚠️  Some tests failed - check the output above")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()
