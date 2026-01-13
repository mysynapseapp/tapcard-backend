from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from routers.auth import get_current_user
from datetime import datetime

router = APIRouter()

@router.get("/api/user/work-experience", response_model=List[schemas.WorkExperienceOut])
def get_work_experiences(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Get all work experiences for the current user"""
    try:
        experiences = db.query(models.WorkExperience).filter(
            models.WorkExperience.user_id == current_user.id
        ).all()
        # Convert each ORM object to Pydantic model with proper serialization
        return [schemas.WorkExperienceOut.from_orm(exp) for exp in experiences]
    except Exception as e:
        print(f"Work experience fetch error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch work experiences: {str(e)}")

@router.post("/api/user/work-experience", response_model=schemas.WorkExperienceOut, status_code=status.HTTP_201_CREATED)
def create_work_experience(
    experience: schemas.WorkExperienceCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Create a new work experience entry"""
    try:
        new_exp = models.WorkExperience(
            user_id=current_user.id,
            company_name=experience.company_name,
            role=experience.role,
            start_date=experience.start_date,
            end_date=experience.end_date,
            description=experience.description,
            created_at=datetime.utcnow()
        )
        db.add(new_exp)
        db.commit()
        db.refresh(new_exp)
        # Convert the ORM object to the Pydantic model with proper serialization
        return schemas.WorkExperienceOut.from_orm(new_exp)
    except Exception as e:
        db.rollback()
        print(f"Error creating work experience: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create work experience: {str(e)}")

@router.put("/api/user/work-experience/{exp_id}", response_model=schemas.WorkExperienceOut)
def update_work_experience(
    exp_id: str, 
    experience_update: schemas.WorkExperienceUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Update an existing work experience entry"""
    try:
        exp = db.query(models.WorkExperience).filter(
            models.WorkExperience.id == exp_id, 
            models.WorkExperience.user_id == current_user.id
        ).first()
        
        if not exp:
            raise HTTPException(status_code=404, detail="Work experience not found")
            
        update_data = experience_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(exp, key, value)
            
        db.commit()
        db.refresh(exp)
        # Convert the ORM object to the Pydantic model with proper serialization
        return schemas.WorkExperienceOut.from_orm(exp)
    except Exception as e:
        db.rollback()
        print(f"Error updating work experience: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update work experience: {str(e)}")

@router.delete("/api/user/work-experience/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_experience(
    exp_id: str, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Delete a work experience entry"""
    try:
        exp = db.query(models.WorkExperience).filter(
            models.WorkExperience.id == exp_id, 
            models.WorkExperience.user_id == current_user.id
        ).first()
        
        if not exp:
            raise HTTPException(status_code=404, detail="Work experience not found")
            
        db.delete(exp)
        db.commit()
        return
    except Exception as e:
        db.rollback()
        print(f"Error deleting work experience: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete work experience: {str(e)}")
