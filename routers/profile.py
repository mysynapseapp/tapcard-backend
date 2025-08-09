from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime
import uuid

import models, schemas
from database import get_db
from routers.auth import oauth2_scheme, verify_password, get_password_hash

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
        # Simple query without joinedload to avoid potential issues
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Load social links separately if needed
        social_links = db.query(models.SocialLink).filter(
            models.SocialLink.user_id == current_user.id
        ).all()
        
        # Create response with social links
        user_out = schemas.UserOut.from_orm(user)
        user_out.social_links = [schemas.SocialLinkOut.from_orm(link) for link in social_links]
        
        return user_out
        
    except Exception as e:
        print(f"Profile fetch error: {str(e)}")
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
            if len(update_data['username']) < 3:
                raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
            if len(update_data['username']) > 50:
                raise HTTPException(status_code=400, detail="Username must be less than 50 characters")
        
        for key, value in update_data.items():
            setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return schemas.UserOut.from_orm(user)
    except Exception as e:
        db.rollback()
        print(f"Profile update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
