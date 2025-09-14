import requests
import json

# Test the reset-password-direct endpoint
BASE_URL = "http://localhost:8000"

def test_reset_password_direct():
    """Test the direct password reset endpoint"""
    
    # Test data - replace with actual test user email
    test_email = "masarukaze041@gmail.com"  # Replace with a real test user email
    new_password = "123456"
    
    payload = {
        "email": test_email,
        "new_password": new_password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password-direct",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Password reset successful!")
        elif response.status_code == 404:
            print("⚠️  User not found (expected for test email)")
        else:
            print("❌ Password reset failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_reset_password_direct()
