from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from jose import JWTError, jwt
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer

import models, schemas
from database import get_db

# ---------------- JWT CONFIG ---------------- #
SECRET_KEY = "your_jwt_secret_key"  # ⚠️ Use environment variable in production
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
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


# ---------------- ROUTES ---------------- #

@router.get("/api/user/portfolio", response_model=List[schemas.PortfolioItemOut])
def get_portfolio_items(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get all portfolio items for the current user"""
    try:
        items = db.query(models.PortfolioItem).filter(
            models.PortfolioItem.user_id == current_user.id
        ).all()
        # Convert each ORM object to Pydantic model with proper serialization
        return [schemas.PortfolioItemOut.from_orm(item) for item in items]
    except Exception as e:
        print(f"Portfolio items fetch error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolio items: {str(e)}")


@router.post("/api/user/portfolio", response_model=schemas.PortfolioItemOut, status_code=status.HTTP_201_CREATED)
def create_portfolio_item(
    item: schemas.PortfolioItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new portfolio item"""
    try:
        # Convert Pydantic URL to string for storage
        media_url_str = str(item.media_url) if item.media_url else None
        
        new_item = models.PortfolioItem(
            user_id=current_user.id,
            title=item.title,
            description=item.description,
            media_url=media_url_str,
            created_at=datetime.utcnow()
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        # Convert the ORM object to the Pydantic model with proper serialization
        return schemas.PortfolioItemOut.from_orm(new_item)
    except Exception as e:
        db.rollback()
        print(f"Error creating portfolio item: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create portfolio item: {str(e)}")


@router.put("/api/user/portfolio/{item_id}", response_model=schemas.PortfolioItemOut)
def update_portfolio_item(
    item_id: str,  # Changed from int to str to match UUID
    item_update: schemas.PortfolioItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update an existing portfolio item"""
    try:
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
        # Convert Pydantic URL to string if media_url is being updated
        if 'media_url' in update_data and update_data['media_url'] is not None:
            update_data['media_url'] = str(update_data['media_url'])
            
        for key, value in update_data.items():
            setattr(item, key, value)

        db.commit()
        db.refresh(item)
        # Convert the ORM object to the Pydantic model with proper serialization
        return schemas.PortfolioItemOut.from_orm(item)
    except Exception as e:
        db.rollback()
        print(f"Error updating portfolio item: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update portfolio item: {str(e)}")
    return item


@router.delete("/api/user/portfolio/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item(
    item_id: str,  # Changed from int to str to match UUID
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a portfolio item"""
    try:
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
    except Exception as e:
        db.rollback()
        print(f"Error deleting portfolio item: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete portfolio item: {str(e)}")
