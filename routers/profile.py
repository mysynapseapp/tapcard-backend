from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime
import uuid

import models, schemas
from database import get_db
from routers.auth import oauth2_scheme

router = APIRouter()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    from jose import JWTError, jwt
    SECRET_KEY = "your-secret-key"
    ALGORITHM = "HS256"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as e:
        # Log JWT errors for debugging
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        print(f"User not found for email: {email}")
        raise credentials_exception
    return user

@router.get("/profile", response_model=schemas.UserOut)
def read_profile(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Get user with all relationships
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return user data using the schema's from_orm method
        return schemas.UserOut.from_orm(user)
        
    except Exception as e:
        print(f"Profile fetch error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch profile: {str(e)}"
        )

@router.put("/profile", response_model=schemas.UserOut)
def update_profile(user_update: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Validate username if provided
        if 'username' in update_data and update_data['username']:
            username = update_data['username'].strip()
            if len(username) < 3:
                raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
            if len(username) > 50:
                raise HTTPException(status_code=400, detail="Username must be less than 50 characters")
            
            # Check if username is already taken by another user
            existing_user = db.query(models.User).filter(
                models.User.username == username,
                models.User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already taken")
        
        # Validate fullname if provided
        if 'fullname' in update_data and update_data['fullname']:
            fullname = update_data['fullname'].strip()
            if len(fullname) < 2:
                raise HTTPException(status_code=400, detail="Full name must be at least 2 characters")
            if len(fullname) > 100:
                raise HTTPException(status_code=400, detail="Full name must be less than 100 characters")
        
        # Validate email if provided
        if 'email' in update_data and update_data['email']:
            email = update_data['email'].strip()
            # Check if email is already taken by another user
            existing_user = db.query(models.User).filter(
                models.User.email == email,
                models.User.id != current_user.id
            ).first()
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
    Get public user profile by user ID
    This endpoint is publicly accessible and returns user details without authentication
    """
    try:
        # Convert string user_id to UUID
        from uuid import UUID
        user_uuid = UUID(user_id)
        
        # Query user with all related data
        user = db.query(models.User).filter(models.User.id == user_uuid).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return user profile using the new UserProfile schema
        return schemas.UserProfile.from_orm(user)
        
    except ValueError:
        # Handle invalid UUID format
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        print(f"Error fetching user profile: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch user profile: {str(e)}")
