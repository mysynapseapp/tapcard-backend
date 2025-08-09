#!/usr/bin/env python3
"""
Comprehensive test script for all tapcard backend endpoints
Tests with credentials: curltest@example.com / curltest123
"""

import requests
import json
import sys
from typing import Dict, Any

class TapCardTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.test_email = "curltest@example.com"
        self.test_password = "curltest123"
        self.test_username = "curltest"
        self.test_full_name = "Test User"
        
    def print_result(self, test_name: str, success: bool, details: str = ""):
        """Print test results with consistent formatting"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
        
    def test_health_check(self) -> bool:
        """Test if the API is running"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.status_code == 200
        except:
            return False
            
    def test_registration(self) -> bool:
        """Test user registration endpoint"""
        try:
            data = {
                "email": self.test_email,
                "password": self.test_password,
                "username": self.test_username,
                "full_name": self.test_full_name
            }
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=data
            )
            
            if response.status_code == 201:
                self.print_result("Registration", True, "User created successfully")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                self.print_result("Registration", True, "User already exists (expected)")
                return True
            else:
                self.print_result("Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("Registration", False, str(e))
            return False
            
    def test_login(self) -> bool:
        """Test login endpoint"""
        try:
            data = {
                "username": self.test_email,
                "password": self.test_password
            }
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get("access_token")
                self.print_result("Login", True, f"Token received: {self.token[:20]}...")
                return True
            else:
                self.print_result("Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("Login", False, str(e))
            return False
            
    def test_profile_get(self) -> bool:
        """Test getting user profile"""
        if not self.token:
            self.print_result("Profile GET", False, "No token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.session.get(
                f"{self.base_url}/api/user/profile",
                headers=headers
            )
            
            if response.status_code == 200:
                profile = response.json()
                self.print_result("Profile GET", True, f"Retrieved profile for {profile.get('email')}")
                return True
            else:
                self.print_result("Profile GET", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("Profile GET", False, str(e))
            return False
            
    def test_profile_update(self) -> bool:
        """Test updating user profile"""
        if not self.token:
            self.print_result("Profile UPDATE", False, "No token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            data = {
                "full_name": "Updated Test User",
                "bio": "Updated bio for testing"
            }
            response = self.session.put(
                f"{self.base_url}/api/user/profile",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                profile = response.json()
                self.print_result("Profile UPDATE", True, f"Updated profile for {profile.get('email')}")
                return True
            else:
                self.print_result("Profile UPDATE", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("Profile UPDATE", False, str(e))
            return False
            
    def test_social_links(self) -> bool:
        """Test social links endpoints"""
        if not self.token:
            self.print_result("Social Links GET", False, "No token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test GET social links
            response = self.session.get(
                f"{self.base_url}/api/user/social-links",
                headers=headers
            )
            
            if response.status_code == 200:
                links = response.json()
                self.print_result("Social Links GET", True, f"Retrieved {len(links)} social links")
                return True
            else:
                self.print_result("Social Links GET", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("Social Links GET", False, str(e))
            return False
            
    def test_work_experience(self) -> bool:
        """Test work experience endpoints"""
        if not self.token:
            self.print_result("Work Experience GET", False, "No token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test GET work experience
            response = self.session.get(
                f"{self.base_url}/api/user/work-experience",
                headers=headers
            )
            
            if response.status_code == 200:
                experiences = response.json()
                self.print_result("Work Experience GET", True, f"Retrieved {len(experiences)} work experiences")
                return True
            else:
                self.print_result("Work Experience GET", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("Work Experience GET", False, str(e))
            return False
            
    def test_portfolio(self) -> bool:
        """Test portfolio endpoints"""
        if not self.token:
            self.print_result("Portfolio GET", False, "No token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test GET portfolio
            response = self.session.get(
                f"{self.base_url}/api/user/portfolio",
                headers=headers
            )
            
            if response.status_code == 200:
                portfolio = response.json()
                self.print_result("Portfolio GET", True, f"Retrieved portfolio data")
                return True
            else:
                self.print_result("Portfolio GET", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("Portfolio GET", False, str(e))
            return False
            
    def test_qr_code(self) -> bool:
        """Test QR code endpoints"""
        if not self.token:
            self.print_result("QR Code GET", False, "No token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test GET QR code
            response = self.session.get(
                f"{self.base_url}/api/user/qr-code",
                headers=headers
            )
            
            if response.status_code == 200:
                qr_data = response.json()
                self.print_result("QR Code GET", True, f"Retrieved QR code data")
                return True
            else:
                self.print_result("QR Code GET", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("QR Code GET", False, str(e))
            return False
            
    def run_all_tests(self):
        """Run all endpoint tests"""
        print("🚀 Starting TapCard Backend Endpoint Tests")
        print("=" * 50)
        print(f"Testing with: {self.test_email} / {self.test_password}")
        print(f"Base URL: {self.base_url}")
        print("=" * 50)
        
        # Check if API is running
        if not self.test_health_check():
            print("❌ API server is not running. Please start it with:")
            print("   cd tapcard-backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
            return
            
        # Run tests
        tests = [
            self.test_registration,
            self.test_login,
            self.test_profile_get,
            self.test_profile_update,
            self.test_social_links,
            self.test_work_experience,
            self.test_portfolio,
            self.test_qr_code
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
                
        print("=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! The backend is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")

if __name__ == "__main__":
    # Allow custom base URL from command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = TapCardTester(base_url)
    tester.run_all_tests()
