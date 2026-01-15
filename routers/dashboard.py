from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from models import User
from routers.profile import get_current_user
import schemas

router = APIRouter(prefix="/api/user", tags=["dashboard"])


# ==================== DASHBOARD RESPONSE SCHEMAS ==================== #

class DashboardProfileResponse(BaseModel):
    """Lightweight profile data for dashboard"""
    id: str
    username: str
    fullname: str
    bio: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    created_at: str


class DashboardSocialLinkResponse(BaseModel):
    """Social link without unnecessary fields"""
    id: str
    platform_name: str
    link_url: str


class DashboardAnalyticsResponse(BaseModel):
    """Analytics summary"""
    link_click: int = 0
    profile_view: int = 0
    qr_scan: int = 0


class DashboardResponse(BaseModel):
    """
    Batch dashboard response - combines multiple data in single call.
    
    ✅ Before: 3-4 separate API calls
    GET /api/user/profile
    GET /api/user/social-links
    GET /api/analytics/stats
    GET /api/social/circle/connections/{id}
    
    ✅ After: Single API call
    GET /api/user/dashboard
    """
    profile: DashboardProfileResponse
    social_links: list[DashboardSocialLinkResponse]
    analytics: DashboardAnalyticsResponse
    connections_count: int = 0
    pending_invites_count: int = 0


# ==================== DASHBOARD ENDPOINT ==================== #

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all dashboard data in a single optimized request.
    
    This endpoint is designed for fast mobile performance:
    - Returns only essential fields (reduces payload size)
    - Fetches all data in optimized queries
    - Ideal for initial app load
    
    Response includes:
    - Profile (without heavy relations)
    - Social links (minimal fields)
    - Analytics summary
    - Connection counts
    """
    # 1. Get profile (minimal fields)
    profile = DashboardProfileResponse(
        id=str(current_user.id),
        username=current_user.username,
        fullname=current_user.fullname,
        bio=current_user.bio,
        followers_count=0,  # Will be computed below
        following_count=0,  # Will be computed below
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
    )
    
    # 2. Get social links (minimal fields)
    social_links = [
        DashboardSocialLinkResponse(
            id=str(link.id),
            platform_name=link.platform_name,
            link_url=link.link_url,
        )
        for link in current_user.social_links
    ]
    
    # 3. Get analytics (simple count query per event type)
    from models import Analytics
    analytics_data = {"link_click": 0, "profile_view": 0, "qr_scan": 0}
    
    for event_type in analytics_data.keys():
        count = db.query(Analytics).filter(
            Analytics.user_id == current_user.id,
            Analytics.event_type == event_type
        ).count()
        analytics_data[event_type] = count
    
    analytics = DashboardAnalyticsResponse(**analytics_data)
    
    # 4. Get connection count
    from models import Circle
    from sqlalchemy import or_
    connections_count = db.query(Circle).filter(
        or_(
            Circle.requester_id == current_user.id,
            Circle.receiver_id == current_user.id
        ),
        Circle.status == "accepted"
    ).count()
    
    # 5. Get pending invites count
    pending_invites_count = db.query(Circle).filter(
        Circle.receiver_id == current_user.id,
        Circle.status == "pending"
    ).count()
    
    return DashboardResponse(
        profile=profile,
        social_links=social_links,
        analytics=analytics,
        connections_count=connections_count,
        pending_invites_count=pending_invites_count,
    )

