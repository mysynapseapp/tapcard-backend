import io
import base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

import qrcode
import models, schemas
from database import get_db
from routers.auth import oauth2_scheme

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

def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@router.get("/", response_model=schemas.QRCodeOut)
def get_qr_code(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    qr_code = db.query(models.QRCode).filter(models.QRCode.user_id == current_user.id).order_by(models.QRCode.last_generated_at.desc()).first()
    if qr_code:
        return qr_code
    # Generate new QR code if none exists
    data = f"https://example.com/user/{current_user.id}"
    qr_code_url = generate_qr_code(data)
    new_qr = models.QRCode(user_id=current_user.id, qr_code_url=qr_code_url, last_generated_at=datetime.utcnow())
    db.add(new_qr)
    db.commit()
    db.refresh(new_qr)
    return new_qr

@router.post("/regenerate", response_model=schemas.QRCodeOut)
def regenerate_qr_code(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    data = f"https://example.com/user/{current_user.id}"
    qr_code_url = generate_qr_code(data)
    new_qr = models.QRCode(user_id=current_user.id, qr_code_url=qr_code_url, last_generated_at=datetime.utcnow())
    db.add(new_qr)
    db.commit()
    db.refresh(new_qr)
    return new_qr
