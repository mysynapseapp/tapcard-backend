from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi.security import OAuth2PasswordBearer

import models, schemas
from database import get_db
from routers.auth import oauth2_scheme
from datetime import datetime

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
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/", response_model=List[schemas.SocialLinkOut])
def get_social_links(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    links = db.query(models.SocialLink).filter(models.SocialLink.user_id == current_user.id).all()
    return links

@router.post("/", response_model=schemas.SocialLinkOut, status_code=status.HTTP_201_CREATED)
def create_social_link(social_link: schemas.SocialLinkCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_link = models.SocialLink(
        user_id=current_user.id,
        platform_name=social_link.platform_name,
        link_url=social_link.link_url
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link

@router.put("/{link_id}", response_model=schemas.SocialLinkOut)
def update_social_link(link_id: str, social_link_update: schemas.SocialLinkUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    link = db.query(models.SocialLink).filter(models.SocialLink.id == link_id, models.SocialLink.user_id == current_user.id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Social link not found")
    update_data = social_link_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(link, key, value)
    db.commit()
    db.refresh(link)
    return link

@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_link(link_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    link = db.query(models.SocialLink).filter(models.SocialLink.id == link_id, models.SocialLink.user_id == current_user.id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Social link not found")
    db.delete(link)
    db.commit()
    return
