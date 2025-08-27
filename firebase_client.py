import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException, status
import os

# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
        # For development, you can use a service account JSON file
        # cred = credentials.Certificate("path/to/serviceAccountKey.json")
        # firebase_admin.initialize_app(cred)
        
        # For production, use environment variables
        firebase_config = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n') if os.getenv("FIREBASE_PRIVATE_KEY") else None,
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
        }
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            
    except Exception as e:
        print(f"Firebase initialization error: {str(e)}")
        raise

# Initialize Firebase on import
try:
    initialize_firebase()
except:
    print("Firebase initialization failed. Please set up environment variables.")

async def create_user_with_email_and_password(email: str, password: str, display_name: str = None):
    try:
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        return user_record
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}"
        )

async def sign_in_with_email_and_password(email: str, password: str):
    try:
        # Firebase Admin SDK doesn't have direct sign-in method
        # This would typically be handled on the client side
        # For backend verification, we'll verify the ID token
        return {"message": "Sign-in should be handled client-side with Firebase Auth SDK"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

async def verify_id_token(id_token: str):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )

async def send_password_reset_email(email: str):
    try:
        # Get user by email to verify they exist
        user = auth.get_user_by_email(email)
        
        # Use Firebase's built-in send_password_reset_email function
        # This will send the email directly through Firebase's email service
        auth.generate_password_reset_link(email)
        
        # Note: Firebase Admin SDK's generate_password_reset_link() generates the link
        # but doesn't send it automatically. For automatic email sending, you would need to:
        # 1. Configure Firebase Authentication email templates in the Firebase Console
        # 2. Use a third-party email service to send the generated link
        # 3. Or use Firebase's client-side SDK for password reset functionality
        
        print(f"Password reset link generated for {email}")
        print("Note: In production, configure Firebase email templates or use an email service")
        
        return {"message": "If the email exists, a reset link will be sent."}
        
    except auth.UserNotFoundError:
        # Don't reveal that the user doesn't exist for security reasons
        return {"message": "If the email exists, a reset link will be sent."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )

async def get_user_by_email(email: str):
    try:
        user = auth.get_user_by_email(email)
        return user
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}"
        )

async def update_user_password(uid: str, new_password: str):
    try:
        auth.update_user(uid, password=new_password)
        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password update failed: {str(e)}"
        )
