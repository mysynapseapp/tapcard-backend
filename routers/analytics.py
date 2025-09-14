from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import models, schemas
from database import get_db
import firebase_admin
from firebase_admin import auth as firebase_auth

router = APIRouter()
security = HTTPBearer()

# Make sure Firebase Admin is initialized somewhere in your app
# Example:
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


class AnalyticsCreate(BaseModel):
    event_type: str
    event_data: str = None


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
    from sqlalchemy import func
    stats = db.query(
        models.Analytics.event_type,
        func.count(models.Analytics.id).label('count')
    ).filter(
        models.Analytics.user_id == current_user.id
    ).group_by(models.Analytics.event_type).all()

    result = {}
    for event_type, count in stats:
        result[event_type] = count

    # Ensure all expected stats are present
    expected_stats = ['link_click', 'profile_view', 'qr_scan']
    for stat in expected_stats:
        if stat not in result:
            result[stat] = 0

    return result
