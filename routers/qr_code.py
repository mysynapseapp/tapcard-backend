import io
import base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import qrcode
import models, schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter()

def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@router.get("/api/user/qr-code", response_model=schemas.QRCodeOut)
def get_qr_code(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Get or generate QR code for the current user"""
    try:
        qr_code = db.query(models.QRCode).filter(
            models.QRCode.user_id == current_user.id
        ).first()

        if not qr_code:
            # Generate a new QR code if none exists
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://yourapp.com/users/{current_user.username}"
            qr_code = models.QRCode(
                user_id=current_user.id,
                qr_code_url=qr_code_url,
                last_generated_at=datetime.utcnow()
            )
            db.add(qr_code)
            db.commit()
            db.refresh(qr_code)
        
        # Convert the ORM object to the Pydantic model with proper serialization
        return schemas.QRCodeOut.from_orm(qr_code)
    except Exception as e:
        db.rollback()
        print(f"Error getting QR code: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get QR code: {str(e)}")

@router.post("/api/user/qr-code/regenerate", response_model=schemas.QRCodeOut)
def regenerate_qr_code(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Regenerate QR code for the current user"""
    try:
        # First, try to find existing QR code
        qr_code = db.query(models.QRCode).filter(
            models.QRCode.user_id == current_user.id
        ).first()

        # Generate new QR code data and URL
        data = f"https://yourapp.com/users/{current_user.username}"
        qr_code_url = generate_qr_code(data)
        
        if qr_code:
            # Update existing QR code
            qr_code.qr_code_url = qr_code_url
            qr_code.last_generated_at = datetime.utcnow()
        else:
            # Create new QR code if none exists
            qr_code = models.QRCode(
                user_id=current_user.id,
                qr_code_url=qr_code_url,
                last_generated_at=datetime.utcnow()
            )
            db.add(qr_code)
        
        db.commit()
        db.refresh(qr_code)
        
        # Convert the ORM object to the Pydantic model with proper serialization
        return schemas.QRCodeOut.from_orm(qr_code)
    except Exception as e:
        db.rollback()
        print(f"Error regenerating QR code: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to regenerate QR code: {str(e)}")
