import firebase_admin
from firebase_admin import auth, credentials
import os
import asyncio
from fastapi import HTTPException, status
from dotenv import load_dotenv

# ---------------------- Load .env ---------------------- #
load_dotenv()  # Automatically loads .env in the current working directory

# ---------------------- Firebase Initialization ---------------------- #

def initialize_firebase():
    if firebase_admin._apps:
        return  # already initialized

    required_vars = [
        "FIREBASE_TYPE",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_PRIVATE_KEY_ID",
        "FIREBASE_PRIVATE_KEY",
        "FIREBASE_CLIENT_EMAIL",
        "FIREBASE_CLIENT_ID",
        "FIREBASE_AUTH_URI",
        "FIREBASE_TOKEN_URI",
        "FIREBASE_AUTH_PROVIDER_CERT_URL",
        "FIREBASE_CLIENT_CERT_URL",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"❌ Missing Firebase environment variables: {missing}")

    # Build Firebase credential dictionary
    firebase_config = {
        "type": os.getenv("FIREBASE_TYPE"),
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
    }

    try:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {str(e)}")
        raise

# Initialize Firebase on import
initialize_firebase()

# ---------------------- Token Verification ---------------------- #

async def verify_id_token(id_token: str):
    """
    Verifies a Firebase ID token asynchronously.
    Raises HTTPException(401) if token is invalid or expired.
    """
    loop = asyncio.get_event_loop()
    try:
        decoded_token = await loop.run_in_executor(None, auth.verify_id_token, id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token verification failed: {str(e)}")
