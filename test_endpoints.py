import requests
import json
import time
import uuid
from datetime import date

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"

# Test user credentials
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "fullname": "Test User"
}

# Global variables to store tokens and IDs
access_token = None
user_id = None
social_link_id = None
portfolio_item_id = None
work_exp_id = None

def print_separator(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def test_root_endpoint():
    """Test the root endpoint"""
    print_separator("Testing Root Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            print(f"Response: {response.json()}")
        else:
            print("❌ Root endpoint failed")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing root endpoint: {e}")

def test_user_registration():
    """Test user registration"""
    print_separator("Testing User Registration")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=TEST_USER)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 201:
            print("✅ User registration successful")
            print(f"Response: {response.json()}")
        elif response.status_code == 400:
            print("ℹ️ User might already exist, continuing...")
        else:
            print("❌ User registration failed")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing user registration: {e}")

def test_user_login():
    """Test user login"""
    print_separator("Testing User Login")
    global access_token
    try:
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            print("✅ User login successful")
            print(f"Access Token: {access_token[:50]}...")
        else:
            print("❌ User login failed")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing user login: {e}")

def get_auth_headers():
    """Get authorization headers"""
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {}

def test_get_me():
    """Test get current user endpoint"""
    print_separator("Testing Get Current User")
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            global user_id
            data = response.json()
            user_id = data.get("id")
            print("✅ Get current user successful")
            print(f"User ID: {user_id}")
        else:
            print("❌ Get current user failed")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing get current user: {e}")

def test_get_profile():
    """Test get user profile"""
    print_separator("Testing Get User Profile")
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Get user profile successful")
            print(f"Profile data: {response.json()}")
        else:
            print("❌ Get user profile failed")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing get user profile: {e}")

def test_update_profile():
    """Test update user profile"""
    print_separator("Testing Update User Profile")
    try:
        headers = get_auth_headers()
        update_data = {
            "bio": "Updated bio from test script",
            "fullname": "Updated Test User"
        }
        response = requests.put(f"{BASE_URL}/api/user/profile", json=update_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Update user profile successful")
            print(f"Updated profile: {response.json()}")
        else:
            print("❌ Update user profile failed")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing update user profile: {e}")

def test_social_links():
    """Test social links CRUD operations"""
    global social_link_id
    print_separator("Testing Social Links")
    
    headers = get_auth_headers()
    if not headers:
        return

    # Test create social link
    social_link_data = {
        "platform_name": "GitHub",
        "link_url": "https://github.com/testuser"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/social-links",
            json=social_link_data,
            headers=headers
        )
        print(f"Create Social Link Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            social_link_id = data.get('id')
            print(f"✅ Social link created with ID: {social_link_id}")
        else:
            print(f"❌ Failed to create social link: {response.text}")
            return

        # Test get all social links
        response = requests.get(
            f"{BASE_URL}/api/user/social-links",
            headers=headers
        )
        print(f"Get Social Links Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Retrieved social links")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to get social links: {response.text}")

        # Test update social link
        if social_link_id:
            update_data = {"platform_name": "GitHub Updated", "link_url": "https://github.com/updated"}
            response = requests.put(f"{BASE_URL}/api/user/social-links/{social_link_id}", json=update_data, headers=headers)
            print(f"Update Social Link Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Social link updated")
            else:
                print(f"❌ Failed to update social link: {response.text}")

    except Exception as e:
        print(f"❌ Error in social links test: {e}")

def test_portfolio():
    """Test portfolio CRUD operations"""
    global portfolio_item_id
    print_separator("Testing Portfolio")
    
    headers = get_auth_headers()
    if not headers:
        return

    # Test create portfolio item
    portfolio_data = {
        "title": "Test Project",
        "description": "A test project description",
        "media_url": "https://example.com/project.jpg"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/portfolio",
            json=portfolio_data,
            headers=headers
        )
        print(f"Create Portfolio Item Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            portfolio_item_id = data.get('id')
            print(f"✅ Portfolio item created with ID: {portfolio_item_id}")
        else:
            print(f"❌ Failed to create portfolio item: {response.text}")
            return

        # Test get all portfolio items
        response = requests.get(
            f"{BASE_URL}/api/user/portfolio",
            headers=headers
        )
        print(f"Get Portfolio Items Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Retrieved portfolio items")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to get portfolio items: {response.text}")

    except Exception as e:
        print(f"❌ Error in portfolio test: {e}")

def test_work_experience():
    """Test work experience CRUD operations"""
    global work_exp_id
    print_separator("Testing Work Experience")
    
    headers = get_auth_headers()
    if not headers:
        return

    # Test create work experience
    work_exp_data = {
        "company_name": "Test Company",
        "role": "Test Role",
        "start_date": "2020-01-01",
        "end_date": "2022-12-31",
        "description": "Test work experience description"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/work-experience",
            json=work_exp_data,
            headers=headers
        )
        print(f"Create Work Experience Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            work_exp_id = data.get('id')
            print(f"✅ Work experience created with ID: {work_exp_id}")
        else:
            print(f"❌ Failed to create work experience: {response.text}")
            return

        # Test get all work experiences
        response = requests.get(
            f"{BASE_URL}/api/user/work-experience",
            headers=headers
        )
        print(f"Get Work Experiences Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Retrieved work experiences")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to get work experiences: {response.text}")

        # Test update work experience
        if work_exp_id:
            update_data = {"role": "Updated Role", "description": "Updated description"}
            response = requests.put(
                f"{BASE_URL}/api/user/work-experience/{work_exp_id}", 
                json=update_data, 
                headers=headers
            )
            print(f"Update Work Experience Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Work experience updated")
            else:
                print(f"❌ Failed to update work experience: {response.text}")

    except Exception as e:
        print(f"❌ Error in work experience test: {e}")

def test_qr_code():
    """Test QR code endpoints"""
    print_separator("Testing QR Code")
    
    headers = get_auth_headers()
    if not headers:
        return
    
    try:
        # Test get QR code
        response = requests.get(
            f"{BASE_URL}/api/user/qr-code",
            headers=headers
        )
        print(f"Get QR Code Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Retrieved QR code")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to get QR code: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in QR code test: {e}")

def test_analytics():
    """Test analytics endpoints"""
    print_separator("Testing Analytics")
    
    headers = get_auth_headers()
    if not headers:
        return
    
    # Test record analytics event
    event_data = {
        "event_type": "profile_view",
        "metadata": {"source": "test"}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analytics",
            json=event_data,
            headers=headers
        )
        print(f"Record Analytics Event Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ Recorded analytics event")
        else:
            print(f"❌ Failed to record analytics event: {response.text}")
            return

        # Test get analytics
        response = requests.get(
            f"{BASE_URL}/api/analytics",
            headers=headers
        )
        print(f"Get Analytics Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Retrieved analytics")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to get analytics: {response.text}")

        # Test get analytics stats
        response = requests.get(
            f"{BASE_URL}/api/analytics/stats",
            headers=headers
        )
        print(f"Get Analytics Stats Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Retrieved analytics stats")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to get analytics stats: {response.text}")

    except Exception as e:
        print(f"❌ Error in analytics test: {e}")

def test_social_features():
    """Test social features like search and follow"""
    print_separator("Testing Social Features")
    
    headers = get_auth_headers()
    if not headers:
        return
    
    try:
        # Test search users
        response = requests.get(
            f"{BASE_URL}/api/social/search",
            params={"q": "test"},
            headers=headers
        )
        print(f"Search Users Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Searched users")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to search users: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in social features test: {e}")

def cleanup_test_data():
    """Clean up test data"""
    print_separator("Cleaning Up Test Data")
    
    headers = get_auth_headers()
    if not headers:
        return
    
    try:
        # Delete social link if it exists
        if social_link_id:
            response = requests.delete(
                f"{BASE_URL}/api/user/social-links/{social_link_id}",
                headers=headers
            )
            print(f"Delete Social Link Status: {response.status_code}")
            if response.status_code == 204:
                print("✅ Deleted test social link")
            else:
                print(f"❌ Failed to delete social link: {response.text}")
        
        # Delete portfolio item if it exists
        if portfolio_item_id:
            response = requests.delete(
                f"{BASE_URL}/api/user/portfolio/{portfolio_item_id}",
                headers=headers
            )
            print(f"Delete Portfolio Item Status: {response.status_code}")
            if response.status_code == 204:
                print("✅ Deleted test portfolio item")
            else:
                print(f"❌ Failed to delete portfolio item: {response.text}")
        
        # Delete work experience if it exists
        if work_exp_id:
            response = requests.delete(
                f"{BASE_URL}/api/user/work-experience/{work_exp_id}",
                headers=headers
            )
            print(f"Delete Work Experience Status: {response.status_code}")
            if response.status_code == 204:
                print("✅ Deleted test work experience")
            else:
                print(f"❌ Failed to delete work experience: {response.text}")
        
        # Delete test user
        if user_id:
            response = requests.delete(
                f"{BASE_URL}/api/user",
                headers=headers
            )
            print(f"Delete User Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Deleted test user")
            else:
                print(f"❌ Failed to delete user: {response.text}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def run_all_tests():
    """Run all test functions"""
    print("🚀 Starting Backend API Tests")
    print(f"Base URL: {BASE_URL}")

    # Basic endpoints
    test_root_endpoint()

    # Auth endpoints
    test_user_registration()
    test_user_login()

    if not access_token:
        print("❌ Cannot proceed without access token. Stopping tests.")
        return

    # User endpoints
    test_get_me()
    test_get_profile()
    test_update_profile()

    # Feature endpoints
    test_social_links()
    test_portfolio()
    test_work_experience()
    test_qr_code()
    test_analytics()
    test_social_features()

    # Cleanup
    cleanup_test_data()

    print_separator("Test Summary")
    print("✅ All tests completed!")
    print("Note: Some endpoints may require additional setup or data for full testing.")

if __name__ == "__main__":
    run_all_tests()
