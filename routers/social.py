from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List
from uuid import UUID

from database import get_db
from models import User, Circle
import schemas
from schemas import UserCircleSearchResponse, CircleStatusEnum, CircleInviteResponse, ConnectionsResponse, PendingInvitesResponse
from routers.profile import get_current_user

router = APIRouter(prefix="/api/social", tags=["social"])


def get_connection_status(db: Session, current_user_id: UUID, other_user_id: UUID) -> tuple[str, bool]:
    """
    Get connection status between two users.
    Returns: (status: "connected" | "pending" | "none", is_invited_by_me: bool)
    """
    # Check if connected
    circle = db.query(Circle).filter(
        or_(
            and_(Circle.requester_id == current_user_id, Circle.receiver_id == other_user_id),
            and_(Circle.requester_id == other_user_id, Circle.receiver_id == current_user_id)
        )
    ).first()
    
    if not circle:
        return "none", False
    
    if circle.status == "accepted":
        return "connected", False
    elif circle.status == "pending":
        if circle.requester_id == current_user_id:
            return "pending", True  # I sent the invite
        else:
            return "pending", False  # They sent the invite
    else:  # rejected
        return "none", False


def get_user_connections_count(db: Session, user_id: UUID) -> int:
    """Get count of accepted connections for a user"""
    return db.query(Circle).filter(
        or_(
            Circle.requester_id == user_id,
            Circle.receiver_id == user_id
        ),
        Circle.status == "accepted"
    ).count()


def build_circle_user_response(db: Session, user: User, current_user_id: UUID) -> UserCircleSearchResponse:
    """Build UserCircleSearchResponse from User object"""
    connection_status, is_invited_by_me = get_connection_status(db, current_user_id, user.id)
    connections_count = get_user_connections_count(db, user.id)
    
    return UserCircleSearchResponse(
        id=str(user.id),
        username=user.username,
        fullname=user.fullname,
        bio=user.bio,
        connection_status=connection_status,
        is_invited_by_me=is_invited_by_me,
        connections_count=connections_count
    )


# ---------------- CIRCLE ROUTES (LinkedIn-style) ---------------- #

@router.post("/circle/invite/{user_id}", response_model=CircleInviteResponse)
def invite_to_circle(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a connection invite to another user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot invite yourself")
    
    user_to_invite = db.query(User).filter(User.id == user_id).first()
    if not user_to_invite:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if there's already a circle relationship
    existing_circle = db.query(Circle).filter(
        or_(
            and_(Circle.requester_id == current_user.id, Circle.receiver_id == user_id),
            and_(Circle.requester_id == user_id, Circle.receiver_id == current_user.id)
        )
    ).first()
    
    if existing_circle:
        if existing_circle.status == "pending":
            if existing_circle.requester_id == current_user.id:
                raise HTTPException(status_code=400, detail="You have already sent an invite to this user")
            else:
                raise HTTPException(status_code=400, detail="This user has already sent you an invite. Please accept or reject it.")
        elif existing_circle.status == "accepted":
            raise HTTPException(status_code=400, detail="You are already connected with this user")
        else:  # rejected - allow re-inviting
            db.delete(existing_circle)
            db.commit()
    
    # Create new circle invite
    circle = Circle(
        requester_id=current_user.id,
        receiver_id=user_id,
        status="pending"
    )
    db.add(circle)
    db.commit()
    db.refresh(circle)
    
    return CircleInviteResponse(
        message="Invite sent successfully",
        circle=schemas.CircleOut.from_orm(circle)
    )


@router.post("/circle/accept/{user_id}", response_model=CircleInviteResponse)
def accept_circle_invite(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a connection invite from another user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot accept invite from yourself")
    
    circle = db.query(Circle).filter(
        Circle.requester_id == user_id,
        Circle.receiver_id == current_user.id,
        Circle.status == "pending"
    ).first()
    
    if not circle:
        raise HTTPException(status_code=404, detail="No pending invite found from this user")
    
    circle.status = "accepted"
    db.commit()
    db.refresh(circle)
    
    return CircleInviteResponse(
        message="Connection accepted successfully",
        circle=schemas.CircleOut.from_orm(circle)
    )


@router.post("/circle/reject/{user_id}", response_model=CircleInviteResponse)
def reject_circle_invite(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a connection invite from another user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot reject invite from yourself")
    
    circle = db.query(Circle).filter(
        Circle.requester_id == user_id,
        Circle.receiver_id == current_user.id,
        Circle.status == "pending"
    ).first()
    
    if not circle:
        raise HTTPException(status_code=404, detail="No pending invite found from this user")
    
    circle.status = "rejected"
    db.commit()
    db.refresh(circle)
    
    return CircleInviteResponse(
        message="Invite rejected",
        circle=schemas.CircleOut.from_orm(circle)
    )


@router.delete("/circle/remove/{user_id}", response_model=CircleInviteResponse)
def remove_circle_connection(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a connection with another user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself from circle")
    
    circle = db.query(Circle).filter(
        or_(
            and_(Circle.requester_id == current_user.id, Circle.receiver_id == user_id),
            and_(Circle.requester_id == user_id, Circle.receiver_id == current_user.id)
        ),
        Circle.status == "accepted"
    ).first()
    
    if not circle:
        raise HTTPException(status_code=404, detail="No connection found with this user")
    
    db.delete(circle)
    db.commit()
    
    return CircleInviteResponse(message="Connection removed successfully")


@router.get("/circle/pending", response_model=PendingInvitesResponse)
def get_pending_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all pending invites (received and sent)"""
    # Get received invites (pending where I am the receiver)
    received_circles = db.query(Circle).filter(
        Circle.receiver_id == current_user.id,
        Circle.status == "pending"
    ).all()
    
    received_users = []
    for circle in received_circles:
        user = db.query(User).filter(User.id == circle.requester_id).first()
        if user:
            received_users.append(build_circle_user_response(db, user, current_user.id))
    
    # Get sent invites (pending where I am the requester)
    sent_circles = db.query(Circle).filter(
        Circle.requester_id == current_user.id,
        Circle.status == "pending"
    ).all()
    
    sent_users = []
    for circle in sent_circles:
        user = db.query(User).filter(User.id == circle.receiver_id).first()
        if user:
            sent_users.append(build_circle_user_response(db, user, current_user.id))
    
    return PendingInvitesResponse(
        received_invites=received_users,
        sent_invites=sent_users
    )


@router.get("/circle/connections/{user_id}", response_model=ConnectionsResponse)
def get_user_connections(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all connections for a user"""
    # Get all accepted circles for the user
    circles = db.query(Circle).filter(
        or_(
            and_(Circle.requester_id == user_id, Circle.status == "accepted"),
            and_(Circle.receiver_id == user_id, Circle.status == "accepted")
        )
    ).all()
    
    connections = []
    for circle in circles:
        # Get the other user in the connection
        other_user_id = circle.receiver_id if circle.requester_id == user_id else circle.requester_id
        user = db.query(User).filter(User.id == other_user_id).first()
        if user:
            connections.append(build_circle_user_response(db, user, current_user.id))
    
    return ConnectionsResponse(
        connections=connections,
        total_count=len(connections)
    )


# ---------------- SEARCH (Updated for Circle) ---------------- #

@router.get("/search", response_model=List[UserCircleSearchResponse])
def search_users(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search users with connection status"""
    users = (
        db.query(User)
        .filter(
            or_(
                User.username.ilike(f"%{q}%"),
                User.fullname.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
            )
        )
        .filter(User.id != current_user.id)  # Exclude self
        .limit(limit)
        .all()
    )

    results = []
    for user in users:
        response = build_circle_user_response(db, user, current_user.id)
        results.append(response)

    return results


# ---------------- BACKWARD COMPATIBILITY (Deprecated) ---------------- #

@router.post("/follow/{user_id}")
def follow_user_deprecated(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """DEPRECATED: Use POST /circle/invite/{user_id} instead"""
    return invite_to_circle(user_id, db, current_user)


@router.delete("/unfollow/{user_id}")
def unfollow_user_deprecated(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """DEPRECATED: Use DELETE /circle/remove/{user_id} instead"""
    return remove_circle_connection(user_id, db, current_user)


@router.get("/followers/{user_id}", response_model=List[UserCircleSearchResponse])
def get_followers_deprecated(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """DEPRECATED: Use GET /circle/connections/{user_id} instead"""
    return get_user_connections(user_id, db, current_user).connections


@router.get("/following/{user_id}", response_model=List[UserCircleSearchResponse])
def get_following_deprecated(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """DEPRECATED: Use GET /circle/connections/{user_id} instead"""
    return get_user_connections(user_id, db, current_user).connections


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

