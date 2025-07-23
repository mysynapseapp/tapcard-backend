from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

import models, schemas
from database import get_db
from routers.auth import oauth2_scheme
from datetime import datetime

router = APIRouter()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    from jose import JWTError, jwt
    SECRET_KEY = "your-secret-key"
    ALGORITHM = "HS256"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
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
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

class AnalyticsCreate(BaseModel):
    event_type: str
    event_data: str = None

@router.post("/", status_code=status.HTTP_201_CREATED)
def log_event(event: AnalyticsCreate = Body(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
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
def get_analytics(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    events = db.query(models.Analytics).filter(models.Analytics.user_id == current_user.id).order_by(models.Analytics.created_at.desc()).all()
    return events
