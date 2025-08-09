from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, HttpUrl, ConfigDict
from uuid import UUID

# User schemas
class UserBase(BaseModel):
    username: str
    bio: Optional[str] = None
    dob: Optional[date] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    bio: Optional[str] = None
    dob: Optional[date] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    dob: Optional[date] = None

class UserOut(BaseModel):
    id: str
    username: str
    email: str
    bio: Optional[str] = None
    dob: Optional[date] = None
    social_links: List['SocialLinkOut'] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        """Convert ORM object with UUID fields to string"""
        from datetime import datetime
        
        # Load social links from the relationship
        social_links_data = []
        if hasattr(obj, 'social_links') and obj.social_links:
            for link in obj.social_links:
                social_links_data.append({
                    'id': str(link.id),
                    'platform_name': link.platform_name,
                    'link_url': str(link.link_url)
                })
        
        data = {
            'id': str(obj.id),
            'username': obj.username,
            'email': obj.email,
            'bio': obj.bio,
            'dob': obj.dob,
            'social_links': social_links_data,
            'created_at': obj.created_at or datetime.utcnow(),
            'updated_at': obj.updated_at or datetime.utcnow()
        }
        return cls(**data)

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

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        """Convert ORM object with UUID fields to string"""
        data = {
            'id': str(obj.id),
            'platform_name': obj.platform_name,
            'link_url': obj.link_url
        }
        return cls(**data)

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

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

# QR Code schemas
class QRCodeOut(BaseModel):
    id: str
    qr_code_url: str
    last_generated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Analytics schemas
class AnalyticsOut(BaseModel):
    id: str
    event_type: str
    event_data: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
