from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi.security import OAuth2PasswordBearer

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

@router.get("/", response_model=List[schemas.WorkExperienceOut])
def get_work_experiences(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    experiences = db.query(models.WorkExperience).filter(models.WorkExperience.user_id == current_user.id).all()
    return experiences

@router.post("/", response_model=schemas.WorkExperienceOut, status_code=status.HTTP_201_CREATED)
def create_work_experience(experience: schemas.WorkExperienceCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_exp = models.WorkExperience(
        user_id=current_user.id,
        company_name=experience.company_name,
        role=experience.role,
        start_date=experience.start_date,
        end_date=experience.end_date,
        description=experience.description
    )
    db.add(new_exp)
    db.commit()
    db.refresh(new_exp)
    return new_exp

@router.put("/{exp_id}", response_model=schemas.WorkExperienceOut)
def update_work_experience(exp_id: str, experience_update: schemas.WorkExperienceUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    exp = db.query(models.WorkExperience).filter(models.WorkExperience.id == exp_id, models.WorkExperience.user_id == current_user.id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Work experience not found")
    update_data = experience_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(exp, key, value)
    db.commit()
    db.refresh(exp)
    return exp

@router.delete("/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_experience(exp_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    exp = db.query(models.WorkExperience).filter(models.WorkExperience.id == exp_id, models.WorkExperience.user_id == current_user.id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Work experience not found")
    db.delete(exp)
    db.commit()
    return
