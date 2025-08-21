#!/usr/bin/env python3
"""
Test script for user registration and login functionality
This script tests the backend authentication endpoints
"""

import requests
import json
import random
import string
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/auth"
HEADERS = {"Content-Type": "application/json"}

class UserAuthTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.registered_users = []
        self.test_results = []
        
    def generate_test_user(self):
        """Generate random test user data"""
        username = f"testuser_{random.randint(1000, 9999)}"
        email = f"{username}@example.com"
        password = "TestPass123!"
        
        return {
            "username": username,
            "email": email,
            "password": password,
            "fullname": f"Test User {random.randint(100, 999)}"
        }
    
    def test_user_registration(self, user_data=None):
        """Test user registration endpoint"""
        if user_data is None:
            user_data = self.generate_test_user()
            
        print(f"\n📝 Testing registration for: {user_data['username']}")
        
        try:
            response = requests.post(
                f"{self.base_url}/register",
                headers=HEADERS,
                json=user_data
            )
            
            result = {
                "test": "registration",
                "username": user_data["username"],
                "status_code": response.status_code,
                "response": response.json() if response.status_code in [200, 201] else response.text,
                "success": response.status_code in [200, 201],
                "timestamp": datetime.now().isoformat()
            }
            
            if response.status_code in [200, 201]:
                print(f"✅ Registration successful for {user_data['username']}")
                self.registered_users.append({
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                
            self.test_results.append(result)
            return result
            
        except Exception as e:
            print(f"❌ Registration error: {e}")
            result = {
                "test": "registration",
                "username": user_data["username"],
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(result)
            return result
    
    def test_user_login(self, username=None, password=None):
        """Test user login endpoint"""
        if username is None and self.registered_users:
            user = self.registered_users[-1]
            username = user["email"]  # Use email for login as per auth.py
            password = user["password"]
        elif username is None:
            username = "testuser_1234@example.com"
            password = "TestPass123!"
            
        print(f"\n🔐 Testing login for: {username}")
        
        # Use form data for OAuth2PasswordRequestForm
        login_data = {
            "username": username,  # This should be email as per auth.py
            "password": password
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=login_data
            )
            
            result = {
                "test": "login",
                "username": username,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text,
                "success": response.status_code == 200,
                "timestamp": datetime.now().isoformat()
            }
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Login successful for {username}")
                print(f"   Token: {data.get('access_token', 'No token')[:20]}...")
                result["token"] = data.get("access_token")
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                
            self.test_results.append(result)
            return result
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            result = {
                "test": "login",
                "username": username,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(result)
            return result
    
    def test_registration_validation(self):
        """Test registration validation rules"""
        print("\n🔍 Testing registration validation...")
        
        test_cases = [
            {"username": "", "email": "test@test.com", "password": "Test123!", "fullname": "Test"},  # Empty username
            {"username": "ab", "email": "test@test.com", "password": "Test123!", "fullname": "Test"},  # Short username
            {"username": "validuser", "email": "invalid-email", "password": "Test123!", "fullname": "Test"},  # Invalid email
            {"username": "validuser", "email": "test@test.com", "password": "123", "fullname": "Test"},  # Weak password
        ]
        
        for test_case in test_cases:
            self.test_user_registration(test_case)
    
    def test_login_validation(self):
        """Test login validation rules"""
        print("\n🔍 Testing login validation...")
        
        test_cases = [
            {"username": "nonexistent", "password": "Test123!"},  # Non-existent user
            {"username": "testuser", "password": "wrongpassword"},  # Wrong password
            {"username": "", "password": "Test123!"},  # Empty username
            {"username": "testuser", "password": ""},  # Empty password
        ]
        
        for test_case in test_cases:
            self.test_user_login(test_case["username"], test_case["password"])
    
    def run_comprehensive_tests(self, num_registrations=3):
        """Run comprehensive test suite"""
        print("🚀 Starting comprehensive user auth testing...")
        
        # Test valid registrations
        print("\n📋 Testing valid registrations...")
        for i in range(num_registrations):
            self.test_user_registration()
        
        # Test login with registered users
        print("\n📋 Testing login with registered users...")
        for user in self.registered_users:
            self.test_user_login(user["email"], user["password"])
        
        # Test validation rules
        self.test_registration_validation()
        self.test_login_validation()
        
        # Summary
        print("\n📊 Test Summary:")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        # Save results
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print("\n✅ Testing complete! Results saved to test_results.json")
        return self.test_results

def main():
    """Main test runner"""
    tester = UserAuthTester()
    
    # Run comprehensive tests
    results = tester.run_comprehensive_tests(num_registrations=3)
    
    # Print failed tests for debugging
    failed_tests = [r for r in results if not r["success"]]
    if failed_tests:
        print("\n❌ Failed tests:")
        for test in failed_tests:
            print(f"  - {test['test']} for {test.get('username', 'unknown')}: {test.get('error', test.get('response', 'Unknown error'))}")

if __name__ == "__main__":
    main()
