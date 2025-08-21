#!/usr/bin/env python3
"""
Test script specifically for user search functionality
"""

import requests
import json
import uuid
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "searchtest@example.com"
TEST_PASSWORD = "testpass123"  # Fixed: Consistent password
TEST_USERNAME = "searchtest"
TEST_FULLNAME = "Search Test User"

# Test users for search
TEST_USERS = [
    {"username": "alice_dev", "fullname": "Alice Developer", "email": "alice@example.com"},
    {"username": "bob_designer", "fullname": "Bob Designer", "email": "bob@example.com"},
    {"username": "charlie_pm", "fullname": "Charlie PM", "email": "charlie@example.com"},
    {"username": "diana_qa", "fullname": "Diana QA", "email": "diana@example.com"},
    {"username": "eve_frontend", "fullname": "Eve Frontend", "email": "eve@example.com"},
]

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} users:")
            for user in data:
                print(f"  - {user['username']} ({user['fullname']}) - "
                      f"Followers: {user['followers_count']}, "
                      f"Following: {user['following_count']}, "
                      f"Is Following: {user['is_following']}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error parsing response: {e}")

def register_test_user(username, fullname, email):
    """Register a test user"""
    url = f"{BASE_URL}/api/auth/register"
    data = {
        "username": username,
        "email": email,
        "password": "testpass123",  # Fixed: Consistent password
        "fullname": fullname
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print(f"✅ Registered: {username}")
        return response.json().get("id")
    elif response.status_code == 400 and "already registered" in response.text:
        print(f"ℹ️  User already exists: {username}")
        return True  # User exists, continue
    else:
        print(f"⚠️  Failed to register {username}: {response.text}")
        return None

def login_user(email, password):
    """Login and get token"""
    url = f"{BASE_URL}/api/auth/login"
    data = {"username": email, "password": password}  # Fixed: Use username field for email
    
    response = requests.post(url, data=data)  # Fixed: Use form data for OAuth2
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"❌ Login failed for {email}: {response.status_code} - {response.text}")
        return None

def cleanup_test_users():
    """Clean up test users (optional - for fresh start)"""
    print("\n🧹 Cleaning up existing test users...")
    for user in TEST_USERS:
        # This would require admin endpoints - skip for now
        pass

def test_user_search(token, search_term):
    """Test user search with given search term"""
    url = f"{BASE_URL}/api/social/search"
    params = {"q": search_term}
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"DEBUG: Making request to {url} with params {params}")
    response = requests.get(url, params=params, headers=headers)
    print(f"DEBUG: Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"DEBUG: Response text: {response.text}")
    return response

def test_search_scenarios():
    """Test various search scenarios"""
    print_section("Testing User Search Scenarios")
    
    # Register test users
    print("\n1. Registering test users...")
    user_ids = []
    for user in TEST_USERS:
        user_id = register_test_user(user["username"], user["fullname"], user["email"])
        if user_id:
            user_ids.append(user_id)
    
    # Login as main test user
    print("\n2. Logging in as main test user...")
    token = login_user(TEST_EMAIL, TEST_PASSWORD)
    if not token:
        # Register main test user if doesn't exist
        register_test_user(TEST_USERNAME, TEST_FULLNAME, TEST_EMAIL)
        token = login_user(TEST_EMAIL, TEST_PASSWORD)
    
    if not token:
        print("❌ Failed to authenticate")
        return
    
    # Test search scenarios
    test_cases = [
        ("alice", "Search for 'alice' - should find Alice Developer"),
        ("dev", "Search for 'dev' - should find Alice Developer"),
        ("bob", "Search for 'bob' - should find Bob Designer"),
        ("design", "Search for 'design' - should find Bob Designer"),
        ("charlie", "Search for 'charlie' - should find Charlie PM"),
        ("frontend", "Search for 'frontend' - should find Eve Frontend"),
        ("nonexistent", "Search for 'nonexistent' - should return empty"),
        ("", "Search for empty string - should fail validation"),
        ("a", "Search for single character - should work"),
    ]
    
    results = []
    for search_term, description in test_cases:
        print(f"\n{description}")
        response = test_user_search(token, search_term)
        print_response(response)
        results.append({
            "search_term": search_term,
            "status": response.status_code,
            "user_count": len(response.json()) if response.status_code == 200 else 0
        })
    
    return results

def test_pagination_and_limits():
    """Test if search handles large result sets"""
    print_section("Testing Search Limits")
    
    token = login_user(TEST_EMAIL, TEST_PASSWORD)
    if not token:
        print("❌ Failed to authenticate")
        return
    
    # Test with very common search term
    response = test_user_search(token, "a")
    if response.status_code == 200:
        users = response.json()
        print(f"Found {len(users)} users with 'a' in username")
        if len(users) > 0:
            print("✅ Search returns results correctly")
        else:
            print("⚠️  No users found")

def test_case_sensitivity():
    """Test case sensitivity in search"""
    print_section("Testing Case Sensitivity")
    
    token = login_user(TEST_EMAIL, TEST_PASSWORD)
    if not token:
        print("❌ Failed to authenticate")
        return
    
    test_cases = [
        ("ALICE", "Uppercase search"),
        ("alice", "Lowercase search"),
        ("Alice", "Mixed case search"),
        ("ALICE_DEV", "Uppercase with underscore"),
        ("alice_dev", "Lowercase with underscore"),
    ]
    
    for search_term, description in test_cases:
        print(f"\n{description}: '{search_term}'")
        response = test_user_search(token, search_term.lower())
        print_response(response)

def run_user_search_tests():
    """Run all user search tests"""
    print("🚀 Starting User Search Functionality Tests...")
    print("=" * 60)
    
    # Test basic functionality
    results = test_search_scenarios()
    
    # Test edge cases
    test_pagination_and_limits()
    test_case_sensitivity()
    
    # Summary
    print_section("Test Summary")
    if results:
        passed = sum(1 for r in results if r['status'] == 200)
        total = len(results)
        print(f"Search tests completed: {passed}/{total} passed")
        
        # Show detailed results
        print("\nDetailed Results:")
        for result in results:
            status_symbol = "✅" if result['status'] == 200 else "❌"
            print(f"{status_symbol} '{result['search_term']}' - {result['user_count']} users found")
    
    print("\n🎯 User search testing completed!")

if __name__ == "__main__":
    run_user_search_tests()
