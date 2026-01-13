from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List
from uuid import UUID

from database import get_db
from models import User, Follow
import schemas
from schemas import UserSearchResponse

# ✅ USE SHARED AUTH (single source of truth)
from routers.profile import get_current_user

router = APIRouter(prefix="/api/social", tags=["social"])


# ---------------- FOLLOW ROUTES ---------------- #

@router.post("/follow/{user_id}")
def follow_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    user_to_follow = db.query(User).filter(User.id == user_id).first()
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="User not found")

    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id,
    ).first()

    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")

    db.add(Follow(follower_id=current_user.id, following_id=user_id))
    db.commit()

    return {"message": "Successfully followed user"}


@router.delete("/unfollow/{user_id}")
def unfollow_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id,
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="You are not following this user")

    db.delete(follow)
    db.commit()

    return {"message": "Successfully unfollowed user"}


# ---------------- SEARCH ---------------- #

@router.get("/search", response_model=List[UserSearchResponse])
def search_users(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = (
        db.query(User)
        .filter(
            or_(
                User.username.ilike(f"%{q}%"),
                User.fullname.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
            )
        )
        .limit(limit)
        .all()
    )

    results: List[UserSearchResponse] = []

    for user in users:
        followers_count = db.query(Follow).filter(
            Follow.following_id == user.id
        ).count()

        following_count = db.query(Follow).filter(
            Follow.follower_id == user.id
        ).count()

        is_following = db.query(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user.id,
        ).first() is not None

        results.append(
            UserSearchResponse(
                id=str(user.id),
                username=user.username,
                fullname=user.fullname,
                bio=user.bio,
                followers_count=followers_count,
                following_count=following_count,
                is_following=is_following,
            )
        )

    return results


# ---------------- FOLLOWERS ---------------- #

@router.get("/followers/{user_id}", response_model=List[UserSearchResponse])
def get_followers(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    followers = (
        db.query(User)
        .join(Follow, Follow.follower_id == User.id)
        .filter(Follow.following_id == user_id)
        .all()
    )

    results = []
    for user in followers:
        results.append(
            UserSearchResponse(
                id=str(user.id),
                username=user.username,
                fullname=user.fullname,
                bio=user.bio,
                followers_count=db.query(Follow)
                .filter(Follow.following_id == user.id)
                .count(),
                following_count=db.query(Follow)
                .filter(Follow.follower_id == user.id)
                .count(),
                is_following=db.query(Follow)
                .filter(
                    Follow.follower_id == current_user.id,
                    Follow.following_id == user.id,
                )
                .first()
                is not None,
            )
        )

    return results


# ---------------- FOLLOWING ---------------- #

@router.get("/following/{user_id}", response_model=List[UserSearchResponse])
def get_following(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    following = (
        db.query(User)
        .join(Follow, Follow.following_id == User.id)
        .filter(Follow.follower_id == user_id)
        .all()
    )

    results = []
    for user in following:
        results.append(
            UserSearchResponse(
                id=str(user.id),
                username=user.username,
                fullname=user.fullname,
                bio=user.bio,
                followers_count=db.query(Follow)
                .filter(Follow.following_id == user.id)
                .count(),
                following_count=db.query(Follow)
                .filter(Follow.follower_id == user.id)
                .count(),
                is_following=db.query(Follow)
                .filter(
                    Follow.follower_id == current_user.id,
                    Follow.following_id == user.id,
                )
                .first()
                is not None,
            )
        )

    return results


# ---------------- PUBLIC PROFILE ---------------- #

@router.get("/profile/{user_id}", response_model=schemas.UserProfile)
def get_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas.UserProfile.from_orm(user)
