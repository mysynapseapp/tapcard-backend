from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from jose import JWTError, jwt

import models, schemas
from database import get_db

router = APIRouter()
security = HTTPBearer()

# ---------------- JWT CONFIG ---------------- #
SECRET_KEY = "your_jwt_secret_key"  # ⚠️ Replace with env var in production
ALGORITHM = "HS256"


# ---------------- AUTH HELPER ---------------- #
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Verify JWT token, extract email, and return user object
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ---------------- ROUTES ---------------- #

@router.get("/profile", response_model=schemas.UserOut)
def read_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current authenticated user's profile
    """
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.UserOut.from_orm(user)


@router.put("/profile", response_model=schemas.UserOut)
def update_profile(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update the current user's profile (with validation)
    """
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.dict(exclude_unset=True)

    # Validate username
    if "username" in update_data and update_data["username"]:
        username = update_data["username"].strip()
        if not (3 <= len(username) <= 50):
            raise HTTPException(status_code=400, detail="Username must be 3–50 characters")
        existing_user = (
            db.query(models.User)
            .filter(models.User.username == username, models.User.id != current_user.id)
            .first()
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")

    # Validate fullname
    if "fullname" in update_data and update_data["fullname"]:
        fullname = update_data["fullname"].strip()
        if not (2 <= len(fullname) <= 100):
            raise HTTPException(status_code=400, detail="Full name must be 2–100 characters")

    # Validate email
    if "email" in update_data and update_data["email"]:
        email = update_data["email"].strip()
        existing_user = (
            db.query(models.User)
            .filter(models.User.email == email, models.User.id != current_user.id)
            .first()
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already taken")

    # Apply updates
    for key, value in update_data.items():
        setattr(user, key, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return schemas.UserOut.from_orm(user)


@router.get("/api/user/profile/{user_id}", response_model=schemas.UserProfile)
def get_user_profile_by_id(user_id: str, db: Session = Depends(get_db)):
    """
    Public endpoint: get user profile by ID
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = db.query(models.User).filter(models.User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas.UserProfile.from_orm(user)
