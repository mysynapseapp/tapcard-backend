from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import func
import jwt

import models, schemas
from database import get_db

# JWT Config
JWT_SECRET = "your_jwt_secret_key"  # ⚠️ Use env var in production
JWT_ALGORITHM = "HS256"

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT token: missing email"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token"
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


class AnalyticsCreate(BaseModel):
    event_type: str
    event_data: str | None = None


@router.post("/", status_code=status.HTTP_201_CREATED)
def log_event(
    event: AnalyticsCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_event = models.Analytics(
        user_id=current_user.id,
        event_type=event.event_type,
        event_data=event.event_data,
        created_at=datetime.utcnow()
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return {"message": "Event logged"}


@router.get("/", response_model=List[schemas.AnalyticsOut])
def get_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    events = (
        db.query(models.Analytics)
        .filter(models.Analytics.user_id == current_user.id)
        .order_by(models.Analytics.created_at.desc())
        .all()
    )
    return events


@router.get("/stats")
def get_analytics_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    stats = db.query(
        models.Analytics.event_type,
        func.count(models.Analytics.id).label('count')
    ).filter(
        models.Analytics.user_id == current_user.id
    ).group_by(models.Analytics.event_type).all()

    result = {}
    for event_type, count in stats:
        result[event_type] = count

    expected_stats = ['link_click', 'profile_view', 'qr_scan']
    for stat in expected_stats:
        if stat not in result:
            result[stat] = 0

    return result
