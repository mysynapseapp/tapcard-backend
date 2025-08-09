c#!/usr/bin/env python3
"""
Master test runner for tapcard backend
Runs both database and endpoint tests
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔍 {description}")
    print("-" * 50)
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} error: {str(e)}")
        return False

def check_server_running():
    """Check if the backend server is running"""
    import requests
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    """Main test runner"""
    print("🚀 TapCard Backend Test Suite")
    print("=" * 60)
    print("Testing with credentials: curltest@example.com / curltest123")
    print("=" * 60)
    
    # Check if server is running
    if not check_server_running():
        print("❌ Backend server is not running!")
        print("Please start the server with:")
        print("   cd tapcard-backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print()
        choice = input("Would you like to continue with database tests only? (y/n): ")
        if choice.lower() != 'y':
            sys.exit(1)
    
    # Run database tests
    print("\n📊 Running Database Tests...")
    db_success = run_command("python test_database.py", "Database Tests")
    
    # Run endpoint tests
    print("\n🌐 Running Endpoint Tests...")
    endpoint_success = run_command("python test_all_endpoints.py", "Endpoint Tests")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    
    if db_success and endpoint_success:
        print("🎉 All tests passed successfully!")
        print("✅ Database is properly configured")
        print("✅ All endpoints are working correctly")
        print("✅ Test user curltest@example.com is accessible")
    elif db_success:
        print("⚠️  Database tests passed, but endpoint tests failed")
        print("   Check server status and try again")
    elif endpoint_success:
        print("⚠️  Endpoint tests passed, but database tests failed")
        print("   Check database configuration")
    else:
        print("❌ Both database and endpoint tests failed")
        print("   Check server and database configuration")
    
    print("\n📖 Usage Instructions:")
    print("   python run_tests.py                    # Run all tests")
    print("   python test_database.py                # Run database tests only")
    print("   python test_all_endpoints.py           # Run endpoint tests only")
    print("   python test_all_endpoints.py http://your-server.com  # Test remote server")

if __name__ == "__main__":
    main()
