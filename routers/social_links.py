from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi.security import OAuth2PasswordBearer
import uuid
import re

import models, schemas
from database import get_db
from routers.auth import oauth2_scheme
from datetime import datetime
from fastapi import Request

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

def validate_url_format(url: str, platform: str) -> bool:
    """Validate URL format based on platform"""
    if platform.lower() == 'youtube':
        # YouTube URL validation - comprehensive patterns
        youtube_patterns = [
            # Standard YouTube URLs
            r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+(?:&[\w-]+=[^&]*)*$',
            r'^https?://(?:www\.)?youtube\.com/watch\?.*v=[\w-]+(?:&[\w-]+=[^&]*)*$',
            r'^https?://(?:www\.)?youtube\.com/embed/[\w-]+(?:\?[^&]*)?$',
            r'^https?://(?:www\.)?youtube\.com/v/[\w-]+(?:\?[^&]*)?$',
            r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+(?:\?[^&]*)?$',
            
            # Channel URLs
            r'^https?://(?:www\.)?youtube\.com/channel/[\w-]+(?:/.*)?$',
            r'^https?://(?:www\.)?youtube\.com/c/[\w-]+(?:/.*)?$',
            r'^https?://(?:www\.)?youtube\.com/user/[\w-]+(?:/.*)?$',
            r'^https?://(?:www\.)?youtube\.com/@\w+(?:/.*)?$',
            
            # Shortened URLs
            r'^https?://(?:www\.)?youtu\.be/[\w-]+(?:\?.*)?$',
            
            # Playlist URLs
            r'^https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+(?:&.*)?$',
            r'^https?://(?:www\.)?youtube\.com/watch\?.*list=[\w-]+(?:&.*)?$',
            
            # Live URLs
            r'^https?://(?:www\.)?youtube\.com/live/[\w-]+(?:\?.*)?$'
        ]
        return any(re.match(pattern, url, re.IGNORECASE) for pattern in youtube_patterns)
    return True

@router.get("/", response_model=List[schemas.SocialLinkOut])
def get_social_links(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        links = db.query(models.SocialLink).filter(models.SocialLink.user_id == current_user.id).all()
        return [schemas.SocialLinkOut.from_orm(link) for link in links]
    except Exception as e:
        print(f"Error fetching social links: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch social links")

@router.post("/", response_model=schemas.SocialLinkOut, status_code=status.HTTP_201_CREATED)
def create_social_link(
    social_link: schemas.SocialLinkCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user),
    request: Request = Depends()
):
    try:
        # Validate URL format
        if not validate_url_format(str(social_link.link_url), social_link.platform_name):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid URL format for {social_link.platform_name}. Please provide a valid URL for this platform."
            )
        
        new_link = models.SocialLink(
            user_id=current_user.id,
            platform_name=social_link.platform_name,
            link_url=str(social_link.link_url)
        )
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        return schemas.SocialLinkOut.from_orm(new_link)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error creating social link: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create social link: {str(e)}")

@router.put("/{link_id}", response_model=schemas.SocialLinkOut)
def update_social_link(link_id: str, social_link_update: schemas.SocialLinkUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        # Convert string ID to UUID
        try:
            link_uuid = uuid.UUID(link_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid link ID format")
            
        link = db.query(models.SocialLink).filter(
            models.SocialLink.id == link_uuid, 
            models.SocialLink.user_id == current_user.id
        ).first()
        
        if not link:
            raise HTTPException(status_code=404, detail="Social link not found")
        
        update_data = social_link_update.dict(exclude_unset=True)
        
        # Validate URL format if provided
        if 'link_url' in update_data and 'platform_name' in update_data:
            if not validate_url_format(str(update_data['link_url']), update_data['platform_name']):
                raise HTTPException(status_code=400, detail="Invalid URL format for the specified platform")
        elif 'link_url' in update_data:
            if not validate_url_format(str(update_data['link_url']), link.platform_name):
                raise HTTPException(status_code=400, detail="Invalid URL format for the specified platform")
        
        for key, value in update_data.items():
            setattr(link, key, value)
        
        db.commit()
        db.refresh(link)
        return schemas.SocialLinkOut.from_orm(link)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating social link: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update social link: {str(e)}")

@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_link(link_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        # Convert string ID to UUID
        try:
            link_uuid = uuid.UUID(link_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid link ID format")
            
        link = db.query(models.SocialLink).filter(
            models.SocialLink.id == link_uuid, 
            models.SocialLink.user_id == current_user.id
        ).first()
        
        if not link:
            raise HTTPException(status_code=404, detail="Social link not found")
        
        db.delete(link)
        db.commit()
        return
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting social link: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete social link: {str(e)}")
