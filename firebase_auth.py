"""
Firebase Admin SDK initialization and token verification.
This module handles Firebase token verification for authentication.
"""

import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials."""
    if firebase_admin._apps:
        return  # Already initialized
    
    # Try to use FIREBASE_SERVICE_ACCOUNT env var (JSON string)
    service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    
    if service_account_json:
        try:
            import json
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            return
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse FIREBASE_SERVICE_ACCOUNT JSON: {e}")
    
    # Try to use individual environment variables
    project_id = os.environ.get('FIREBASE_PROJECT_ID')
    if project_id:
        try:
            # Use application default credentials
            firebase_admin.initialize_app(options={'projectId': project_id})
            return
        except Exception as e:
            print(f"Failed to initialize Firebase with project ID: {e}")
    
    # Fallback: Try to use google-application-credentials
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Warning: Firebase Admin SDK not initialized. Auth will fail. Error: {e}")

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

# Initialize on module import
initialize_firebase()

