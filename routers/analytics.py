from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

import models
from database import get_db

# ✅ IMPORT THE EXISTING AUTH FUNCTION
from routers.profile import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


# ---------- Schemas ----------

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


# ---------- Routes ----------

@router.post("", status_code=status.HTTP_201_CREATED, response_model=AnalyticsOut)
async def log_event(
    event: AnalyticsCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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
            "created_at": new_event.created_at,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to log analytics event")


@router.get("", response_model=List[AnalyticsOut])
async def get_analytics(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    events = (
        db.query(models.Analytics)
        .filter(models.Analytics.user_id == current_user.id)
        .order_by(models.Analytics.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(event.id),
            "event_type": event.event_type,
            "event_data": event.event_data,
            "created_at": event.created_at,
        }
        for event in events
    ]


@router.get("/stats", response_model=AnalyticsStats)
async def get_analytics_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    event_counts = (
        db.query(
            models.Analytics.event_type,
            func.count(models.Analytics.id).label("count")
        )
        .filter(models.Analytics.user_id == current_user.id)
        .group_by(models.Analytics.event_type)
        .all()
    )

    stats = {
        "profile_view": 0,
        "link_click": 0,
        "qr_scan": 0,
    }

    for event_type, count in event_counts:
        if event_type in stats:
            stats[event_type] = count

    return stats
