from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
import uuid

import models, schemas
from database import get_db
from firebase_auth import verify_firebase_token

router = APIRouter()
security = HTTPBearer()

# ==============================
# AUTH HELPER
# ==============================
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Verify Firebase token and return the current user.
    Automatically creates a user if not found.
    """

    token = credentials.credentials
    firebase_data = verify_firebase_token(token)

    firebase_uid = firebase_data.get("uid")
    email = firebase_data.get("email")
    name = firebase_data.get("name") or "New User"

    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        )

    user = (
        db.query(models.User)
        .filter(models.User.firebase_uid == firebase_uid)
        .first()
    )

    # ✅ AUTO-CREATE USER IF NOT EXISTS
    if not user:
        user = models.User(
            firebase_uid=firebase_uid,
            email=email,
            fullname=name,
            username=f"user_{uuid.uuid4().hex[:8]}",
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


# ==============================
# ROUTES
# ==============================

@router.get("/profile", response_model=schemas.UserOut)
def read_profile(
    current_user: models.User = Depends(get_current_user),
):
    """
    Get the current authenticated user's profile
    """
    return schemas.UserOut.from_orm(current_user)


@router.put("/profile", response_model=schemas.UserOut)
def update_profile(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update the current user's profile
    """
    user = current_user
    update_data = user_update.dict(exclude_unset=True)

    # ----------------
    # Validate username
    # ----------------
    if "username" in update_data and update_data["username"]:
        username = update_data["username"].strip()
        if not (3 <= len(username) <= 50):
            raise HTTPException(
                status_code=400,
                detail="Username must be 3–50 characters"
            )

        existing_user = (
            db.query(models.User)
            .filter(
                models.User.username == username,
                models.User.id != user.id
            )
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )

        update_data["username"] = username

    # ----------------
    # Validate fullname
    # ----------------
    if "fullname" in update_data and update_data["fullname"]:
        fullname = update_data["fullname"].strip()
        if not (2 <= len(fullname) <= 100):
            raise HTTPException(
                status_code=400,
                detail="Full name must be 2–100 characters"
            )
        update_data["fullname"] = fullname

    # ----------------
    # Validate email
    # ----------------
    if "email" in update_data and update_data["email"]:
        email = update_data["email"].strip()
        existing_user = (
            db.query(models.User)
            .filter(
                models.User.email == email,
                models.User.id != user.id
            )
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already taken"
            )
        update_data["email"] = email

    # ----------------
    # Apply updates
    # ----------------
    for key, value in update_data.items():
        setattr(user, key, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return schemas.UserOut.from_orm(user)


@router.get("/profile/{user_id}", response_model=schemas.UserProfile)
def get_user_profile_by_id(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Public endpoint: get user profile by ID
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID format"
        )

    user = (
        db.query(models.User)
        .filter(models.User.id == user_uuid)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return schemas.UserProfile.from_orm(user)
