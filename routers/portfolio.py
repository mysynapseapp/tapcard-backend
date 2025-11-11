from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from jose import JWTError, jwt
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer

import models, schemas
from database import get_db

# ---------------- JWT CONFIG ---------------- #
SECRET_KEY = "your-secret-key"  # ⚠️ Use environment variable in production
ALGORITHM = "HS256"

# OAuth2 Bearer Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter()


# ---------------- AUTH HELPER ---------------- #
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
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

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


# ---------------- ROUTES ---------------- #

@router.get("/", response_model=List[schemas.PortfolioItemOut])
def get_portfolio_items(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get all portfolio items for the current user"""
    items = (
        db.query(models.PortfolioItem)
        .filter(models.PortfolioItem.user_id == current_user.id)
        .order_by(models.PortfolioItem.created_at.desc())
        .all()
    )
    return items


@router.post("/", response_model=schemas.PortfolioItemOut, status_code=status.HTTP_201_CREATED)
def create_portfolio_item(
    item: schemas.PortfolioItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new portfolio item"""
    new_item = models.PortfolioItem(
        user_id=current_user.id,
        title=item.title,
        description=item.description,
        media_url=item.media_url,
        created_at=datetime.utcnow(),
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.put("/{item_id}", response_model=schemas.PortfolioItemOut)
def update_portfolio_item(
    item_id: int,
    item_update: schemas.PortfolioItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update an existing portfolio item"""
    item = (
        db.query(models.PortfolioItem)
        .filter(
            models.PortfolioItem.id == item_id,
            models.PortfolioItem.user_id == current_user.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a portfolio item"""
    item = (
        db.query(models.PortfolioItem)
        .filter(
            models.PortfolioItem.id == item_id,
            models.PortfolioItem.user_id == current_user.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    db.delete(item)
    db.commit()
    return
