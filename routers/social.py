from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from uuid import UUID
from database import get_db
from models import User, Follow
from schemas import UserSearchResponse, FollowResponse
from routers.auth import get_current_user

router = APIRouter(prefix="/social", tags=["social"])

@router.post("/follow/{user_id}")
def follow_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Follow a user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check if user exists
    user_to_follow = db.query(User).filter(User.id == user_id).first()
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing_follow = db.query(Follow).filter(
        and_(Follow.follower_id == current_user.id, Follow.following_id == user_id)
    ).first()
    
    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")
    
    # Create follow relationship
    follow = Follow(
        follower_id=current_user.id,
        following_id=user_id
    )
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
        raise HTTPException(status_code=404, detail="Not following this user")
    
    db.delete(follow)
    db.commit()
    
    return {"message": "Successfully unfollowed user"}

@router.get("/search", response_model=List[UserSearchResponse])
def search_users(
    username: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search users by username"""
    users = db.query(User).filter(
        User.username.ilike(f"%{username}%")
    ).all()
    
    results = []
    for user in users:
        followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
        following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
        
        # Check if current user is following this user
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

@router.get("/followers/{user_id}", response_model=List[UserSearchResponse])
def get_followers(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get followers of a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    followers = db.query(User).join(
        Follow, User.id == Follow.follower_id
    ).filter(
        Follow.following_id == user_id
    ).all()
    
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
    """Get users that a user is following"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    following = db.query(User).join(
        Follow, User.id == Follow.following_id
    ).filter(
        Follow.follower_id == user_id
    ).all()
    
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
