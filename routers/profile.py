from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

import firebase_admin
from firebase_admin import auth as firebase_auth

import models, schemas
from database import get_db

router = APIRouter()
security = HTTPBearer()

# Make sure Firebase Admin is initialized in your main.py or startup
# Example:
# cred = firebase_admin.credentials.Certificate("path/to/serviceAccountKey.json")
# firebase_admin.initialize_app(cred)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    token = credentials.credentials
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        email = decoded_token.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token")
    except Exception as e:
        print(f"Firebase token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/profile", response_model=schemas.UserOut)
def read_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return schemas.UserOut.from_orm(user)
    except Exception as e:
        print(f"Profile fetch error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")


@router.put("/profile", response_model=schemas.UserOut)
def update_profile(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = user_update.dict(exclude_unset=True)

        # Validate username
        if "username" in update_data and update_data["username"]:
            username = update_data["username"].strip()
            if not (3 <= len(username) <= 50):
                raise HTTPException(status_code=400, detail="Username must be 3-50 characters")
            existing_user = db.query(models.User).filter(models.User.username == username, models.User.id != current_user.id).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already taken")

        # Validate fullname
        if "fullname" in update_data and update_data["fullname"]:
            fullname = update_data["fullname"].strip()
            if not (2 <= len(fullname) <= 100):
                raise HTTPException(status_code=400, detail="Full name must be 2-100 characters")

        # Validate email
        if "email" in update_data and update_data["email"]:
            email = update_data["email"].strip()
            existing_user = db.query(models.User).filter(models.User.email == email, models.User.id != current_user.id).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already taken")

        for key, value in update_data.items():
            setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return schemas.UserOut.from_orm(user)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Profile update error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.get("/api/user/profile/{user_id}", response_model=schemas.UserProfile)
def get_user_profile_by_id(user_id: str, db: Session = Depends(get_db)):
    """
    Public endpoint: get user profile by user ID
    """
    try:
        user_uuid = UUID(user_id)
        user = db.query(models.User).filter(models.User.id == user_uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return schemas.UserProfile.from_orm(user)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        print(f"Error fetching user profile: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch user profile: {str(e)}")
