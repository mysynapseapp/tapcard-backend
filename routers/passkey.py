from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import base64
import json
import uuid
from typing import Dict, Optional

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    RegistrationCredential,
    AuthenticationCredential,
    AuthenticatorTransport,
    AuthenticatorAttachment,
    ResidentKeyRequirement,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
)

import models, schemas
from database import get_db
from routers.auth import create_access_token

router = APIRouter(tags=["passkey"])
security = HTTPBearer()

# Configuration
RP_NAME = "TapCard"
RP_ID = "localhost"  # Update with your domain
ORIGIN = "http://localhost:8000"  # Update with your domain
CHALLENGE_BYTES = 32

# In-memory storage for challenges (consider using Redis in production)
challenge_store: Dict[str, dict] = {}

# Pydantic Models
class PasskeyRegistrationOptionsResponse(schemas.BaseModel):
    options: dict

class PasskeyRegistrationVerification(schemas.BaseModel):
    email: str
    credential: dict
    challenge: str

class PasskeyLoginOptionsResponse(schemas.BaseModel):
    options: dict

class PasskeyLoginVerification(schemas.BaseModel):
    email: str
    credential: dict
    challenge: str

# Helper functions
def generate_challenge() -> str:
    """Generate a random challenge."""
    return base64.urlsafe_b64encode(secrets.token_bytes(CHALLENGE_BYTES)).decode("ascii").rstrip("=")

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Retrieve user by email."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_passkey_credential(db: Session, credential_id: str) -> Optional[models.PasskeyCredential]:
    """Retrieve passkey credential by credential_id."""
    return db.query(models.PasskeyCredential).filter(models.PasskeyCredential.credential_id == credential_id).first()

def save_passkey_credential(
    db: Session, 
    user_id: str, 
    credential_id: str, 
    public_key: str, 
    sign_count: int
) -> models.PasskeyCredential:
    """Save a new passkey credential."""
    credential = models.PasskeyCredential(
        user_id=user_id,
        credential_id=credential_id,
        public_key=public_key,
        sign_count=sign_count,
        created_at=datetime.utcnow()
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential

def update_passkey_sign_count(db: Session, credential_id: str, new_sign_count: int) -> None:
    """Update the sign count for a passkey credential."""
    db.query(models.PasskeyCredential).filter(
        models.PasskeyCredential.credential_id == credential_id
    ).update({
        models.PasskeyCredential.sign_count: new_sign_count,
        models.PasskeyCredential.last_used_at: datetime.utcnow()
    })
    db.commit()

# Routes
@router.get("/register/challenge", response_model=PasskeyRegistrationOptionsResponse)
async def get_registration_challenge(email: str, db: Session = Depends(get_db)):
    """Generate registration options for a new passkey."""
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    challenge = generate_challenge()
    
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(user.id).encode(),
        user_name=user.email,
        user_display_name=user.fullname or user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.PREFERRED,
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            require_resident_key=True,
        ),
    )

    # Store the challenge for later verification
    challenge_store[email] = {
        "challenge": challenge,
        "user_id": str(user.id),
        "type": "registration"
    }

    return {"options": json.loads(options_to_json(options))}

@router.post("/register/verify")
async def verify_registration(
    request: Request,
    data: PasskeyRegistrationVerification,
    db: Session = Depends(get_db)
):
    """Verify the registration of a new passkey."""
    stored_data = challenge_store.get(data.email)
    if not stored_data or stored_data["type"] != "registration":
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")

    try:
        # Get the client data from the request
        client_data = data.credential.get("response", {}).get("clientDataJSON")
        if not client_data:
            raise HTTPException(status_code=400, detail="Missing clientDataJSON in credential")

        # Verify the registration response
        verification = verify_registration_response(
            credential={
                "id": data.credential["id"],
                "rawId": data.credential["rawId"],
                "response": {
                    "clientDataJSON": data.credential["response"]["clientDataJSON"],
                    "attestationObject": data.credential["response"].get("attestationObject", ""),
                    "transports": data.credential["response"].get("transports", []),
                },
                "type": data.credential["type"],
                "clientExtensionResults": data.credential.get("clientExtensionResults", {}),
            },
            expected_challenge=stored_data["challenge"],
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
        )

        # Save the new credential
        credential = save_passkey_credential(
            db=db,
            user_id=stored_data["user_id"],
            credential_id=base64.urlsafe_b64encode(verification.credential_id).decode('utf-8').rstrip("="),
            public_key=base64.urlsafe_b64encode(verification.credential_public_key).decode('utf-8').rstrip("="),
            sign_count=verification.sign_count
        )

        # Clean up
        challenge_store.pop(data.email, None)

        return {
            "status": "success",
            "message": "Passkey registered successfully",
            "credential_id": credential.credential_id
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Verification failed: {str(e)}")

@router.get("/login/challenge", response_model=PasskeyLoginOptionsResponse)
async def get_login_challenge(email: str, db: Session = Depends(get_db)):
    """Generate authentication options for passkey login."""
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's passkey credentials
    credentials = db.query(models.PasskeyCredential).filter(
        models.PasskeyCredential.user_id == str(user.id)
    ).all()

    if not credentials:
        raise HTTPException(status_code=400, detail="No passkeys registered for this user")

    challenge = generate_challenge()
    
    # Prepare allowed credentials
    allow_credentials = [
        {
            "id": cred.credential_id,
            "type": "public-key",
            "transports": ["internal"],
        }
        for cred in credentials
    ]

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    # Store the challenge for later verification
    challenge_store[email] = {
        "challenge": challenge,
        "user_id": str(user.id),
        "type": "authentication"
    }

    return {"options": json.loads(options_to_json(options))}

@router.post("/login/verify")
async def verify_login(
    data: PasskeyLoginVerification,
    db: Session = Depends(get_db)
):
    """Verify the passkey authentication."""
    stored_data = challenge_store.get(data.email)
    if not stored_data or stored_data["type"] != "authentication":
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")

    try:
        # Get the credential ID from the response
        credential_id = data.credential.get("id")
        if not credential_id:
            raise HTTPException(status_code=400, detail="Missing credential ID in response")

        # Get the stored credential
        credential = get_passkey_credential(db, credential_id)
        if not credential or str(credential.user_id) != stored_data["user_id"]:
            raise HTTPException(status_code=400, detail="Invalid credential")

        # Verify the authentication response
        verification = verify_authentication_response(
            credential={
                "id": data.credential["id"],
                "rawId": data.credential["rawId"],
                "response": {
                    "clientDataJSON": data.credential["response"]["clientDataJSON"],
                    "authenticatorData": data.credential["response"].get("authenticatorData", ""),
                    "signature": data.credential["response"].get("signature", ""),
                    "userHandle": data.credential["response"].get("userHandle", ""),
                },
                "type": data.credential["type"],
                "clientExtensionResults": data.credential.get("clientExtensionResults", {}),
            },
            credential_public_key=base64.urlsafe_b64decode(credential.public_key + "=="),
            credential_current_sign_count=credential.sign_count,
            expected_challenge=stored_data["challenge"],
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            require_user_verification=True,
        )

        # Update the sign count
        update_passkey_sign_count(db, credential_id, verification.new_sign_count)

        # Clean up
        challenge_store.pop(data.email, None)

        # Get the user
        user = db.query(models.User).filter(models.User.id == credential.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Generate JWT token (using the existing auth system)
        access_token = create_access_token({"email": user.email})

        return {
            "status": "success",
            "message": "Authentication successful",
            "access_token": access_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.get("/credentials/{user_id}")
async def get_user_credentials(user_id: str, db: Session = Depends(get_db)):
    """Get all passkey credentials for a user."""
    credentials = db.query(models.PasskeyCredential).filter(
        models.PasskeyCredential.user_id == user_id
    ).all()
    
    return [
        {
            "id": str(cred.id),
            "credential_id": cred.credential_id,
            "created_at": cred.created_at,
            "last_used_at": cred.last_used_at
        }
        for cred in credentials
    ]

@router.delete("/credentials/{credential_id}")
async def delete_credential(credential_id: str, db: Session = Depends(get_db)):
    """Delete a passkey credential."""
    credential = get_passkey_credential(db, credential_id)
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    db.delete(credential)
    db.commit()
    
    return {"status": "success", "message": "Credential deleted successfully"}