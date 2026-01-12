"""
Authentication router using Firebase for all auth operations.
Frontend handles Firebase auth (login, register, reset password).
Backend only verifies Firebase tokens and manages user profiles.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
import secrets

import models, schemas
from database import get_db
from firebase_auth import verify_firebase_token, get_user_by_uid

router = APIRouter()
security = HTTPBearer()


# ---------------- Dependency ---------------- #
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Verify Firebase ID token and get user from database.
    The token is a Firebase ID token containing the firebase_uid.
    """
    token = credentials.credentials
    
    # Verify Firebase ID token
    try:
        firebase_data = verify_firebase_token(token)
    except HTTPException:
        raise
    
    firebase_uid = firebase_data.get("uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token: missing uid",
        )

    user = db.query(models.User).filter(models.User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ---------------- Routes ---------------- #

@router.post("/google-login", response_model=schemas.UserOut)
async def google_login(request: schemas.GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Sync Firebase user with backend database.
    
    Frontend sends the Firebase ID token after successful Firebase authentication.
    Backend verifies the token and creates/updates user in database.
    
    Expected body: { "id_token": "firebase_id_token", "username": "desired_username" (optional) }
    """
    # 1. Verify Firebase ID token
    try:
        firebase_data = verify_firebase_token(request.id_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to verify Firebase token: {str(e)}",
        )

    firebase_uid = firebase_data.get("uid")
    email = firebase_data.get("email", "")
    name = firebase_data.get("name", "")

    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token: missing uid",
        )

    # 2. Check if user exists in our database
    user = db.query(models.User).filter(models.User.firebase_uid == firebase_uid).first()

    if user:
        # User exists - update info if needed
        if email and user.email != email:
            user.email = email
        if name and user.fullname != name:
            user.fullname = name
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    else:
        # New user - create in database
        # Use provided username or generate one from email
        username = request.username
        if not username:
            # Generate username from email or name
            if email:
                username = email.split("@")[0]
            elif name:
                username = name.lower().replace(" ", "_")
            else:
                username = f"user_{secrets.token_hex(4)}"

        # Ensure username is unique
        existing_username = db.query(models.User).filter(models.User.username == username).first()
        if existing_username:
            username = f"{username}_{secrets.token_hex(4)}"

        new_user = models.User(
            firebase_uid=firebase_uid,
            username=username,
            email=email,
            fullname=name,
            bio=None,
            dob=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user

    return schemas.UserOut.from_orm(user)


@router.post("/link-account", response_model=schemas.UserOut)
async def link_account(
    request: schemas.LinkAccountRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link an additional Firebase auth method to existing account.
    Or update profile information.
    
    Expected body: { "id_token": "firebase_id_token" }
    """
    # Verify the new Firebase token
    try:
        firebase_data = verify_firebase_token(request.id_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to verify Firebase token: {str(e)}",
        )

    firebase_uid = firebase_data.get("uid")
    email = firebase_data.get("email", "")
    name = firebase_data.get("name", "")

    # Update current user with Firebase data
    if email:
        current_user.email = email
    if name:
        current_user.fullname = name
    current_user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)

    return schemas.UserOut.from_orm(current_user)


@router.get("/me", response_model=schemas.UserOut)
async def get_me(user=Depends(get_current_user)):
    """Get current logged-in user details."""
    return schemas.UserOut.from_orm(user)

