from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

import models, schemas
from database import get_db
from firebase_client import (
    create_user_with_email_and_password,
    verify_id_token,
    send_password_reset_email,
    get_user_by_email as get_firebase_user_by_email,
    update_user_password
)

SECRET_KEY = "your-secret-key"  # Change to secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

@router.post("/register", response_model=schemas.UserOut)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user already exists in database
        if db.query(models.User).filter(models.User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        if db.query(models.User).filter(models.User.username == user.username).first():
            raise HTTPException(status_code=400, detail="Username already taken")
        if len(user.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        # Create user in Firebase
        firebase_user = await create_user_with_email_and_password(
            email=user.email,
            password=user.password,
            display_name=user.fullname
        )

        # Create user in local database
        new_user = models.User(
            username=user.username,
            email=user.email,
            password_hash="firebase_auth",  # Password is managed by Firebase
            fullname=user.fullname,
            bio=user.bio if user.bio else None,
            dob=user.dob if user.dob else None,
            firebase_uid=firebase_user.uid
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return schemas.UserOut.from_orm(new_user)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=schemas.Token)
async def login(login_data: schemas.Login):
    try:
        # For Firebase authentication, the actual login should be handled client-side
        # The client should get the ID token from Firebase and send it to this endpoint
        # For now, we'll verify the user exists in Firebase and generate our tokens
        
        # Check if user exists in Firebase
        firebase_user = await get_firebase_user_by_email(login_data.email)
        if not firebase_user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Generate our own JWT tokens
        access_token = create_access_token(data={"sub": login_data.email})
        refresh_token = create_refresh_token(data={"sub": login_data.email})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(refresh_token: str = Body(...)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(data={"sub": email})
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout():
    # JWT stateless logout - client should delete tokens
    return {"message": "Logout successful"}

@router.post("/forgot-password")
async def forgot_password(email: schemas.Login):
    try:
        result = await send_password_reset_email(email.email)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

@router.post("/reset-password")
async def reset_password(uid: str = Body(...), new_password: str = Body(...)):
    try:
        result = await update_user_password(uid, new_password)
        return {"message": "Password updated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password update failed: {str(e)}")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user
