from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

import models, schemas
from database import get_db
from firebase_client import verify_id_token  # ✅ import firebase verify function

router = APIRouter()
security = HTTPBearer()
# security = HTTPBearer()
oauth2_scheme = security  # ✅ keep compatibility



def get_or_create_user(decoded_token: dict, db: Session):
    uid = decoded_token["uid"]
    email = decoded_token.get("email")
    name = decoded_token.get("name")
    picture = decoded_token.get("picture")

    user = db.query(models.User).filter(models.User.firebase_uid == uid).first()
    if not user:
        user = models.User(
            firebase_uid=uid,
            email=email,
            fullname=name,
            username=email.split("@")[0] if email else uid,  # fallback if no email
            picture=picture,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


async def get_current_user(token=Depends(security), db: Session = Depends(get_db)):
    try:
        decoded_token = await verify_id_token(token.credentials)  # ✅ use firebase client
        return get_or_create_user(decoded_token, db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# ---------------- Routes ---------------- #

@router.post("/google-login", response_model=schemas.UserOut)
async def google_login(user=Depends(get_current_user)):
    """Flutter sends Firebase ID token, backend verifies & returns user profile"""
    return schemas.UserOut.from_orm(user)


@router.get("/me", response_model=schemas.UserOut)
async def get_me(user=Depends(get_current_user)):
    return schemas.UserOut.from_orm(user)
