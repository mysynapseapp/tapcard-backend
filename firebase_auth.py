"""
Firebase Admin SDK initialization and token verification.
This module handles Firebase token verification for authentication.
"""

import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials."""
    print("🔧 Starting Firebase initialization...")
    
    if firebase_admin._apps:
        print("✅ Firebase already initialized")
        return  # Already initialized
    
    # Try to use FIREBASE_SERVICE_ACCOUNT env var (JSON string)
    service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    print(f"🔍 FIREBASE_SERVICE_ACCOUNT: {'set' if service_account_json else 'not set'}")
    
    if service_account_json:
        try:
            import json
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            print("✅ Initialized with FIREBASE_SERVICE_ACCOUNT")
            return
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ Failed to parse FIREBASE_SERVICE_ACCOUNT JSON: {e}")
    
    # Try to use individual environment variables to build service account info
    project_id = os.environ.get('FIREBASE_PROJECT_ID')
    private_key = os.environ.get('FIREBASE_PRIVATE_KEY')
    client_email = os.environ.get('FIREBASE_CLIENT_EMAIL')
    print(f"🔍 FIREBASE_PROJECT_ID: {project_id}")
    print(f"🔍 FIREBASE_PRIVATE_KEY: {'set' if private_key else 'not set'}")
    print(f"🔍 FIREBASE_CLIENT_EMAIL: {client_email}")
    
    if project_id and private_key and client_email:
        try:
            # Build service account info dict from environment variables
            service_account_info = {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": private_key.replace('\\n', '\n'),  # Handle escaped newlines
                "client_email": client_email,
                "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
                "auth_uri": os.environ.get('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
                "token_uri": os.environ.get('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
                "auth_provider_x509_cert_url": os.environ.get('FIREBASE_AUTH_PROVIDER_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
                "client_x509_cert_url": os.environ.get('FIREBASE_CLIENT_CERT_URL')
            }
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            print("✅ Initialized with individual Firebase environment variables")
            return
        except Exception as e:
            print(f"❌ Failed to initialize Firebase with individual env vars: {e}")
    
    # Fallback: Try to use google-application-credentials
    google_creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    print(f"🔍 GOOGLE_APPLICATION_CREDENTIALS: {google_creds_path}")
    if google_creds_path:
        try:
            cred = credentials.Certificate(google_creds_path)
            firebase_admin.initialize_app(cred)
            print("✅ Initialized with GOOGLE_APPLICATION_CREDENTIALS")
            return
        except Exception as e:
            print(f"❌ Failed to initialize Firebase with GOOGLE_APPLICATION_CREDENTIALS: {e}")
    
    # Final fallback: Try to use application default credentials
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        print("✅ Initialized with Application Default Credentials")
    except Exception as e:
        print(f"❌ Warning: Firebase Admin SDK not initialized. Auth will fail. Error: {e}")

def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token and return the decoded claims.
    
    Args:
        id_token: The Firebase ID token to verify
        
    Returns:
        dict: Decoded token claims including 'uid', 'email', 'name', etc.
        
    Raises:
        HTTPException: If token verification fails
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token has expired",
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token has been revoked",
        )
    except auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )

def get_user_by_uid(firebase_uid: str) -> auth.UserRecord:
    """
    Get a Firebase user by their UID.
    
    Args:
        firebase_uid: The Firebase user UID
        
    Returns:
        UserRecord: Firebase user record
        
    Raises:
        HTTPException: If user not found or error occurs
    """
    try:
        return auth.get_user(firebase_uid)
    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firebase user not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Firebase user: {str(e)}",
        )

def delete_user(firebase_uid: str) -> dict:
    """
    Delete a Firebase user by their UID.
    
    Args:
        firebase_uid: The Firebase user UID
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user not found or error occurs
    """
    try:
        auth.delete_user(firebase_uid)
        return {"message": f"User {firebase_uid} deleted successfully from Firebase"}
    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firebase user not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete Firebase user: {str(e)}",
        )

# Initialize on module import
initialize_firebase()

