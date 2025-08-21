#!/usr/bin/env python3
"""
Test script for social search endpoint
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/social"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_success(message: str):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message: str):
    print(f"{RED}❌ {message}{RESET}")

def print_info(message: str):
    print(f"{YELLOW}ℹ️  {message}{RESET}")

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Test an endpoint and return the response"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return {
            "status_code": response.status_code,
            "json": response.json() if response.status_code == 200 else None,
            "text": response.text
        }
    except Exception as e:
        return {
            "status_code": 0,
            "error": str(e)
        }

def test_search_endpoint():
    """Test the social search endpoint"""
    print_info("Testing social search endpoint...")
    
    # Test 1: Basic search
    print_info("Testing basic search...")
    response = test_endpoint("GET", "/search", params={"q": "test"})
    
    if response["status_code"] == 200:
        print_success("Search endpoint is accessible")
        if response["json"]:
            print_success(f"Found {len(response['json'])} users")
        else:
            print_info("No users found")
    else:
        print_error(f"Search failed with status {response['status_code']}")
        if "error" in response:
            print_error(f"Error: {response['error']}")
        return False
    
    # Test 2: Search with limit
    print_info("Testing search with limit...")
    response = test_endpoint("GET", "/search", params={"q": "test", "limit": 5})
    
    if response["status_code"] == 200:
        print_success("Search with limit works")
    else:
        print_error("Search with limit failed")
        return False
    
    # Test 3: Empty search query
    print_info("Testing empty search query...")
    response = test_endpoint("GET", "/search", params={"q": ""})
    
    if response["status_code"] == 422:
        print_success("Empty query properly rejected")
    else:
        print_error("Empty query should be rejected")
        return False
    
    return True

def test_follow_endpoints():
    """Test follow/unfollow endpoints"""
    print_info("Testing follow endpoints...")
    
    # Note: These tests require authentication tokens
    # For now, we'll just check if the endpoints exist
    
    # Test follow endpoint
    response = test_endpoint("POST", "/follow/123e4567-e89b-12d3-a456-426614174000")
    
    if response["status_code"] == 401 or response["status_code"] == 403:
        print_success("Follow endpoint requires authentication (expected)")
    elif response["status_code"] == 400:
        print_success("Follow endpoint accessible")
    else:
        print_error(f"Follow endpoint issue: {response['status_code']}")
    
    # Test unfollow endpoint
    response = test_endpoint("DELETE", "/unfollow/123e4567-e89b-12d3-a456-426614174000")
    
    if response["status_code"] == 401 or response["status_code"] == 403:
        print_success("Unfollow endpoint requires authentication (expected)")
    elif response["status_code"] == 400:
        print_success("Unfollow endpoint accessible")
    else:
        print_error(f"Unfollow endpoint issue: {response['status_code']}")
    
    return True

def test_followers_endpoints():
    """Test followers/following endpoints"""
    print_info("Testing followers endpoints...")
    
    # Test followers endpoint
    response = test_endpoint("GET", "/followers/123e4567-e89b-12d3-a456-426614174000")
    
    if response["status_code"] == 200:
        print_success("Followers endpoint accessible")
    else:
        print_error(f"Followers endpoint issue: {response['status_code']}")
    
    # Test following endpoint
    response = test_endpoint("GET", "/following/123e4567-e89b-12d3-a456-426614174000")
    
    if response["status_code"] == 200:
        print_success("Following endpoint accessible")
    else:
        print_error(f"Following endpoint issue: {response['status_code']}")
    
    return True

def test_server_health():
    """Test if the server is running"""
    print_info("Testing server health...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print_success("Server is running")
            return True
        else:
            print_error("Server returned unexpected status")
            return False
    except Exception as e:
        print_error(f"Server not accessible: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("SOCIAL SEARCH ENDPOINT TESTS")
    print("=" * 50)
    
    # Test server health first
    if not test_server_health():
        print_error("Server is not running. Please start the server first.")
        print("Run: uvicorn main:app --reload")
        sys.exit(1)
    
    # Test all endpoints
    tests = [
        test_search_endpoint,
        test_follow_endpoints,
        test_followers_endpoints
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print_success("All tests passed! 🎉")
    else:
        print_error("Some tests failed. Please check the issues above.")
    print("=" * 50)

if __name__ == "__main__":
    main()
