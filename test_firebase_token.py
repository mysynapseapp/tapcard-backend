from dotenv import load_dotenv
import os

# Load .env from current directory
load_dotenv()

# Optional: check that variables are loaded
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
    print("❌ Missing env variables:", missing)
else:
    print("✅ All Firebase env variables loaded")
