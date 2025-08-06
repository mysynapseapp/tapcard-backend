from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, HttpUrl

# User schemas
class UserBase(BaseModel):
    username: str
    bio: Optional[str] = None
    dob: Optional[date] = None

class UserCreate(BaseModel):
    username: str
    bio: Optional[str] = None
    dob: Optional[date] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    dob: Optional[date] = None

class UserOut(BaseModel):
    id: str
    username: str
    bio: Optional[str] = None
    dob: Optional[date] = None
    social_links: List['SocialLinkOut'] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class Login(BaseModel):
    email: EmailStr
    password: str

# Social Link schemas
class SocialLinkBase(BaseModel):
    platform_name: str
    link_url: HttpUrl

class SocialLinkCreate(SocialLinkBase):
    pass

class SocialLinkUpdate(BaseModel):
    platform_name: Optional[str] = None
    link_url: Optional[HttpUrl] = None

class SocialLinkOut(SocialLinkBase):
    id: str

    class Config:
        orm_mode = True

# Portfolio Item schemas
class PortfolioItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    media_url: Optional[HttpUrl] = None

class PortfolioItemCreate(PortfolioItemBase):
    pass

class PortfolioItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    media_url: Optional[HttpUrl] = None

class PortfolioItemOut(PortfolioItemBase):
    id: str

    class Config:
        orm_mode = True

# Work Experience schemas
class WorkExperienceBase(BaseModel):
    company_name: str
    role: str
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None

class WorkExperienceCreate(WorkExperienceBase):
    pass

class WorkExperienceUpdate(BaseModel):
    company_name: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

class WorkExperienceOut(WorkExperienceBase):
    id: str

    class Config:
        orm_mode = True

# QR Code schemas
class QRCodeOut(BaseModel):
    id: str
    qr_code_url: str
    last_generated_at: datetime

    class Config:
        orm_mode = True

# Analytics schemas
class AnalyticsOut(BaseModel):
    id: str
    event_type: str
    event_data: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
