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
from firebase_auth import verify_firebase_token, get_user_by_uid, delete_user

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


@router.post("/google-login-fast", response_model=schemas.GoogleLoginResponse)
async def google_login_fast(request: schemas.GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Fast Google login endpoint for better UX.
    
    This endpoint returns minimal information (is_new_user, is_profile_complete)
    to allow the frontend to redirect immediately without waiting for full profile.
    
    Expected body: { "id_token": "firebase_id_token", "username": "desired_username" (optional) }
    
    Returns:
        - access_token: Firebase ID token for backend auth
        - is_new_user: True if user was just created
        - user_id: User's UUID
        - is_profile_complete: True if user has completed their profile
        - message: Status message
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

    is_new_user = False
    if not user:
        is_new_user = True
        # Generate username from email or name
        username = request.username
        if not username:
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
            is_profile_complete=False,  # New users must complete profile
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user

    return schemas.GoogleLoginResponse(
        access_token=request.id_token,  # Use Firebase token for backend auth
        is_new_user=is_new_user,
        user_id=str(user.id),
        is_profile_complete=user.is_profile_complete or False,
        message="New user created" if is_new_user else "Returning user"
    )


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


@router.delete("/delete-account")
async def delete_account(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current user's account.
    
    This will:
    1. Delete the user from Firebase Auth
    2. Delete the user from the PostgreSQL database (cascades to all related data)
    
    Returns:
        - Success message
        
    Warning: This action is irreversible!
    """
    firebase_uid = current_user.firebase_uid
    
    # 1. Delete from Firebase
    delete_user(firebase_uid)
    
    # 2. Delete from database (cascade deletes related data)
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}


