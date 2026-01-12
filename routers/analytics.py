from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import jwt
import models, schemas
from database import get_db

# JWT Config
JWT_SECRET = "your_jwt_secret_key"  # ⚠️ Use env var in production
JWT_ALGORITHM = "HS256"

router = APIRouter()
security = HTTPBearer()

class AnalyticsCreate(BaseModel):
    event_type: str
    event_data: Optional[str] = None

class AnalyticsStats(BaseModel):
    profile_view: int = 0
    link_click: int = 0
    qr_scan: int = 0

class AnalyticsOut(BaseModel):
    id: str
    event_type: str
    event_data: Optional[str] = None
    created_at: datetime

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AnalyticsOut)
async def log_event(
    event: AnalyticsCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Log an analytics event"""
    try:
        new_event = models.Analytics(
            user_id=current_user.id,
            event_type=event.event_type,
            event_data=event.event_data,
            created_at=datetime.utcnow()
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        
        return {
            "id": str(new_event.id),
            "event_type": new_event.event_type,
            "event_data": new_event.event_data,
            "created_at": new_event.created_at
        }
    except Exception as e:
        db.rollback()
        print(f"Error logging analytics event: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to log analytics event: {str(e)}")


@router.get("", response_model=List[AnalyticsOut])
async def get_analytics(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get analytics events for the current user"""
    try:
        events = db.query(models.Analytics).filter(
            models.Analytics.user_id == current_user.id
        ).order_by(models.Analytics.created_at.desc()).offset(skip).limit(limit).all()
        
        return [{
            "id": str(event.id),
            "event_type": event.event_type,
            "event_data": event.event_data,
            "created_at": event.created_at
        } for event in events]
    except Exception as e:
        print(f"Error fetching analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")


@router.get("/stats", response_model=AnalyticsStats)
async def get_analytics_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get analytics statistics for the current user"""
    try:
        # Get count of each event type
        event_counts = db.query(
            models.Analytics.event_type,
            func.count(models.Analytics.id).label("count")
        ).filter(
            models.Analytics.user_id == current_user.id
        ).group_by(models.Analytics.event_type).all()
        
        # Initialize default stats
        stats = {
            'profile_view': 0,
            'link_click': 0,
            'qr_scan': 0
        }
        
        # Update with actual counts from the database
        for event_type, count in event_counts:
            if event_type in stats:
                stats[event_type] = count
        
        return stats
    except Exception as e:
        print(f"Error fetching analytics stats: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return default stats in case of error
        return {
            'profile_view': 0,
            'link_click': 0,
            'qr_scan': 0
        }
    return result
