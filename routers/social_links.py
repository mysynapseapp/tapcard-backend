from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import re
from datetime import datetime

import models, schemas
from database import get_db
import firebase_admin
from firebase_admin import auth as firebase_auth

router = APIRouter()
security = HTTPBearer()

# Initialize Firebase Admin somewhere in your app (main.py or startup)
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token"
            )
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


def validate_url_format(url: str, platform: str) -> bool:
    """Validate URL format based on platform"""
    if platform.lower() == 'youtube':
        youtube_patterns = [
            r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+(?:&[\w-]+=[^&]*)*$',
            r'^https?://(?:www\.)?youtube\.com/embed/[\w-]+(?:\?[^&]*)?$',
            r'^https?://(?:www\.)?youtu\.be/[\w-]+(?:\?.*)?$',
            r'^https?://(?:www\.)?youtube\.com/channel/[\w-]+(?:/.*)?$',
            r'^https?://(?:www\.)?youtube\.com/c/[\w-]+(?:/.*)?$',
            r'^https?://(?:www\.)?youtube\.com/user/[\w-]+(?:/.*)?$',
            r'^https?://(?:www\.)?youtube\.com/@\w+(?:/.*)?$',
            r'^https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+(?:&.*)?$',
            r'^https?://(?:www\.)?youtube\.com/watch\?.*list=[\w-]+(?:&.*)?$',
            r'^https?://(?:www\.)?youtube\.com/live/[\w-]+(?:\?.*)?$'
        ]
        return any(re.match(pattern, url, re.IGNORECASE) for pattern in youtube_patterns)
    return True


@router.get("/social-links", response_model=List[schemas.SocialLinkOut])
def get_social_links(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        links = db.query(models.SocialLink).filter(models.SocialLink.user_id == current_user.id).all()
        return [schemas.SocialLinkOut.from_orm(link) for link in links]
    except Exception as e:
        print(f"Error fetching social links: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch social links")


@router.post("/social-links", response_model=schemas.SocialLinkOut, status_code=status.HTTP_201_CREATED)
def create_social_link(
    social_link: schemas.SocialLinkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        if not validate_url_format(str(social_link.link_url), social_link.platform_name):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid URL format for {social_link.platform_name}"
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


@router.put("/social-links/{link_id}", response_model=schemas.SocialLinkOut)
def update_social_link(
    link_id: str,
    social_link_update: schemas.SocialLinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
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

        if 'link_url' in update_data:
            platform = update_data.get('platform_name', link.platform_name)
            if not validate_url_format(str(update_data['link_url']), platform):
                raise HTTPException(status_code=400, detail="Invalid URL format for the platform")
            update_data['link_url'] = str(update_data['link_url'])

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


@router.delete("/social-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_link(
    link_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
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
