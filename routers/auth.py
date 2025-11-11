from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt

import models, schemas
from database import get_db

router = APIRouter()
security = HTTPBearer()

# ✅ JWT Config
JWT_SECRET = "your_jwt_secret_key"  # ⚠️ Replace with env var in production
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 1 day


# ---------------- JWT Utility Functions ---------------- #
def create_access_token(data: dict):
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ---------------- Dependency ---------------- #
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Verify JWT and get user"""
    token = credentials.credentials
    payload = decode_access_token(token)
    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ---------------- Routes ---------------- #

@router.post("/login", response_model=schemas.TokenOut)
def login_user(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    User login route — validates credentials, returns JWT token.
    Expected body: { "email": "user@example.com", "password": "1234" }
    """
    user = db.query(models.User).filter(models.User.email == login_data.email).first()

    if not user or user.password != login_data.password:  # ⚠️ In prod, hash passwords!
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
async def get_me(user=Depends(get_current_user)):
    """Get current logged-in user details"""
    return schemas.UserOut.from_orm(user)
