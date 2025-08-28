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
    fullname: str
    bio: Optional[str] = None
    dob: Optional[date] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    fullname: Optional[str] = None
    bio: Optional[str] = None
    dob: Optional[date] = None

class UserOut(BaseModel):
    id: str
    username: str
    email: str
    fullname: str
    bio: Optional[str] = None
    dob: Optional[date] = None
    social_links: List['SocialLinkOut'] = []
    followers_count: int = 0
    following_count: int = 0
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
                social_links_data.append(SocialLinkOut.from_orm(link))
        
        # Calculate followers and following counts
        followers_count = len(obj.followers) if hasattr(obj, 'followers') and obj.followers else 0
        following_count = len(obj.following) if hasattr(obj, 'following') and obj.following else 0
        
        # Handle missing created_at/updated_at
        created_at = obj.created_at if hasattr(obj, 'created_at') and obj.created_at else datetime.utcnow()
        updated_at = obj.updated_at if hasattr(obj, 'updated_at') and obj.updated_at else datetime.utcnow()
        
        data = {
            'id': str(obj.id),
            'username': obj.username,
            'email': obj.email,
            'fullname': obj.fullname,
            'bio': obj.bio,
            'dob': obj.dob,
            'social_links': social_links_data,
            'followers_count': followers_count,
            'following_count': following_count,
            'created_at': created_at,
            'updated_at': updated_at
        }
        return cls(**data)

class UserProfile(BaseModel):
    id: str
    username: str
    fullname: str
    bio: Optional[str] = None
    dob: Optional[date] = None
    social_links: List['SocialLinkOut'] = []
    portfolio_items: List['PortfolioItemOut'] = []
    work_experiences: List['WorkExperienceOut'] = []
    followers_count: int = 0
    following_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        """Convert ORM object with UUID fields to string for public profile"""
        from datetime import datetime
        
        # Load social links
        social_links_data = []
        if hasattr(obj, 'social_links') and obj.social_links:
            for link in obj.social_links:
                social_links_data.append(SocialLinkOut.from_orm(link))
        
        # Load portfolio items
        portfolio_items_data = []
        if hasattr(obj, 'portfolio_items') and obj.portfolio_items:
            for item in obj.portfolio_items:
                portfolio_items_data.append(PortfolioItemOut.from_orm(item))
        
        # Load work experiences
        work_experiences_data = []
        if hasattr(obj, 'work_experiences') and obj.work_experiences:
            for exp in obj.work_experiences:
                work_experiences_data.append(WorkExperienceOut.from_orm(exp))
        
        # Calculate followers and following counts
        followers_count = len(obj.followers) if hasattr(obj, 'followers') and obj.followers else 0
        following_count = len(obj.following) if hasattr(obj, 'following') and obj.following else 0
        
        # Handle missing created_at
        created_at = obj.created_at if hasattr(obj, 'created_at') and obj.created_at else datetime.utcnow()
        
        data = {
            'id': str(obj.id),
            'username': obj.username,
            'fullname': obj.fullname,
            'bio': obj.bio,
            'dob': obj.dob,
            'social_links': social_links_data,
            'portfolio_items': portfolio_items_data,
            'work_experiences': work_experiences_data,
            'followers_count': followers_count,
            'following_count': following_count,
            'created_at': created_at
        }
        return cls(**data)

# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class Login(BaseModel):
    email: EmailStr
    password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    new_password: str

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

# Social schemas
class UserSearchResponse(BaseModel):
    id: str
    username: str
    fullname: str
    bio: Optional[str] = None
    followers_count: int
    following_count: int
    is_following: bool

    model_config = ConfigDict(from_attributes=True)

class FollowResponse(BaseModel):
    message: str

    model_config = ConfigDict(from_attributes=True)
