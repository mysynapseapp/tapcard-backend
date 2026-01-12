import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base

def generate_uuid():
    return uuid.uuid4()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, unique=True, index=True)
    firebase_uid = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True, index=True)  # Nullable for Google-only users
    fullname = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    dob = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    social_links = relationship("SocialLink", back_populates="user", cascade="all, delete-orphan")
    portfolio_items = relationship("PortfolioItem", back_populates="user", cascade="all, delete-orphan")
    work_experiences = relationship("WorkExperience", back_populates="user", cascade="all, delete-orphan")
    qr_codes = relationship("QRCode", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")
    passkey_credentials = relationship("PasskeyCredential", back_populates="user", cascade="all, delete-orphan")
    
    # Follow relationships
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following", cascade="all, delete-orphan")

class Follow(Base):
    __tablename__ = "follows"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, unique=True, index=True)
    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    following_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")

class SocialLink(Base):
    __tablename__ = "social_links"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    platform_name = Column(String, nullable=False)
    link_url = Column(String, nullable=False)

    user = relationship("User", back_populates="social_links")

class PortfolioItem(Base):
    __tablename__ = "portfolio_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="portfolio_items")

class WorkExperience(Base):
    __tablename__ = "work_experience"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="work_experiences")

class QRCode(Base):
    __tablename__ = "qr_codes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    qr_code_url = Column(String, nullable=False)
    last_generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="qr_codes")

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)  # e.g., qr_scan, link_click
    event_data = Column(Text, nullable=True)  # JSON string with details like geo/IP, link clicked, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analytics")


class PasskeyCredential(Base):
    __tablename__ = "passkey_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    credential_id = Column(String, unique=True, nullable=False)
    public_key = Column(Text, nullable=False)
    sign_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="passkey_credentials")
