from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from uuid import UUID
from jose import JWTError, jwt
from database import get_db
from models import User, Follow
import schemas
from schemas import UserSearchResponse
from datetime import datetime

router = APIRouter(prefix="", tags=["social"])
security = HTTPBearer()

# ---------------- JWT CONFIG ---------------- #
SECRET_KEY = "your_jwt_secret_key"  # ⚠️ use environment variable in production
ALGORITHM = "HS256"


# ---------------- AUTH HELPER ---------------- #
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify JWT token and return current user
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=401,
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

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ---------------- FOLLOW ROUTES ---------------- #

@router.post("/follow/{user_id}")
def follow_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Follow another user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    user_to_follow = db.query(User).filter(User.id == user_id).first()
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="User not found")

    existing_follow = db.query(Follow).filter(
        and_(Follow.follower_id == current_user.id, Follow.following_id == user_id)
    ).first()
    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")

    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    db.commit()
    return {"message": "Successfully followed user"}


@router.delete("/unfollow/{user_id}")
def unfollow_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unfollow a user"""
    follow = db.query(Follow).filter(
        and_(Follow.follower_id == current_user.id, Follow.following_id == user_id)
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="You are not following this user")

    db.delete(follow)
    db.commit()
    return {"message": "Successfully unfollowed user"}


# ---------------- SEARCH ROUTES ---------------- #

@router.get("/search", response_model=List[UserSearchResponse])
def search_users(
    q: str = Query(..., min_length=1, description="Search query for username, fullname, or email"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for users by username, fullname, or email"""
    try:
        username_results = db.query(User).filter(User.username.ilike(f"%{q}%")).limit(limit).all()
        name_results = db.query(User).filter(User.fullname.ilike(f"%{q}%")).limit(limit).all()
        email_results = db.query(User).filter(User.email.ilike(f"%{q}%")).limit(limit).all()

        all_users = list({user.id: user for user in (username_results + name_results + email_results)}.values())
        final_results = all_users[:limit]

        results = []
        for user in final_results:
            followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
            following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()

            is_following = db.query(Follow).filter(
                and_(Follow.follower_id == current_user.id, Follow.following_id == user.id)
            ).first() is not None

            results.append(UserSearchResponse(
                id=str(user.id),
                username=user.username,
                fullname=user.fullname,
                bio=user.bio,
                followers_count=followers_count,
                following_count=following_count,
                is_following=is_following
            ))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# ---------------- FOLLOWERS / FOLLOWING ---------------- #

@router.get("/followers/{user_id}", response_model=List[UserSearchResponse])
def get_followers(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get followers of a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    followers = db.query(User).join(Follow, User.id == Follow.follower_id).filter(Follow.following_id == user_id).all()
    results = []

    for follower in followers:
        followers_count = db.query(Follow).filter(Follow.following_id == follower.id).count()
        following_count = db.query(Follow).filter(Follow.follower_id == follower.id).count()
        is_following = db.query(Follow).filter(
            and_(Follow.follower_id == current_user.id, Follow.following_id == follower.id)
        ).first() is not None

        results.append(UserSearchResponse(
            id=str(follower.id),
            username=follower.username,
            fullname=follower.fullname,
            bio=follower.bio,
            followers_count=followers_count,
            following_count=following_count,
            is_following=is_following
        ))

    return results


@router.get("/following/{user_id}", response_model=List[UserSearchResponse])
def get_following(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the list of users a specific user is following"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    following = db.query(User).join(Follow, User.id == Follow.following_id).filter(Follow.follower_id == user_id).all()
    results = []

    for followed_user in following:
        followers_count = db.query(Follow).filter(Follow.following_id == followed_user.id).count()
        following_count = db.query(Follow).filter(Follow.follower_id == followed_user.id).count()
        is_following = db.query(Follow).filter(
            and_(Follow.follower_id == current_user.id, Follow.following_id == followed_user.id)
        ).first() is not None

        results.append(UserSearchResponse(
            id=str(followed_user.id),
            username=followed_user.username,
            fullname=followed_user.fullname,
            bio=followed_user.bio,
            followers_count=followers_count,
            following_count=following_count,
            is_following=is_following
        ))

    return results


# ---------------- PROFILE ---------------- #

@router.get("/profile/{user_id}", response_model=schemas.UserProfile)
def get_user_profile_with_counts(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user profile (public) with follower/following counts"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.UserProfile.from_orm(user)
