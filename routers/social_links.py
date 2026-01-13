from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import re

import models, schemas
from database import get_db
from routers.profile import get_current_user  # ✅ USE FIREBASE AUTH

router = APIRouter()


# ---------------- VALIDATION HELPER ---------------- #
def validate_url_format(url: str, platform: str) -> bool:
    if platform.lower() == 'youtube':
        youtube_patterns = [
            r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'^https?://(?:www\.)?youtu\.be/[\w-]+',
            r'^https?://(?:www\.)?youtube\.com/@\w+',
            r'^https?://(?:www\.)?youtube\.com/channel/[\w-]+',
        ]
        return any(re.match(p, url, re.IGNORECASE) for p in youtube_patterns)
    return True


# ---------------- ROUTES ---------------- #

@router.get("/api/user/social-links", response_model=List[schemas.SocialLinkOut])
def get_social_links(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.SocialLink)
        .filter(models.SocialLink.user_id == current_user.id)
        .all()
    )


@router.post(
    "/api/user/social-links",
    response_model=schemas.SocialLinkOut,
    status_code=status.HTTP_201_CREATED
)
def create_social_link(
    social_link: schemas.SocialLinkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not validate_url_format(str(social_link.link_url), social_link.platform_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid URL for {social_link.platform_name}"
        )

    new_link = models.SocialLink(
        user_id=current_user.id,
        platform_name=social_link.platform_name,
        link_url=str(social_link.link_url),
    )

    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


@router.put("/api/user/social-links/{link_id}", response_model=schemas.SocialLinkOut)
def update_social_link(
    link_id: str,
    social_link_update: schemas.SocialLinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        link_uuid = uuid.UUID(link_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid link ID")

    link = (
        db.query(models.SocialLink)
        .filter(
            models.SocialLink.id == link_uuid,
            models.SocialLink.user_id == current_user.id
        )
        .first()
    )

    if not link:
        raise HTTPException(status_code=404, detail="Social link not found")

    update_data = social_link_update.dict(exclude_unset=True)

    if "link_url" in update_data:
        platform = update_data.get("platform_name", link.platform_name)
        if not validate_url_format(str(update_data["link_url"]), platform):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        update_data["link_url"] = str(update_data["link_url"])

    for key, value in update_data.items():
        setattr(link, key, value)

    db.commit()
    db.refresh(link)
    return link


@router.delete(
    "/api/user/social-links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_social_link(
    link_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        link_uuid = uuid.UUID(link_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid link ID")

    link = (
        db.query(models.SocialLink)
        .filter(
            models.SocialLink.id == link_uuid,
            models.SocialLink.user_id == current_user.id
        )
        .first()
    )

    if not link:
        raise HTTPException(status_code=404, detail="Social link not found")

    db.delete(link)
    db.commit()
