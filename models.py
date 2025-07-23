import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date, Integer
from sqlalchemy.orm import relationship
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid, unique=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    social_links = relationship("SocialLink", back_populates="user", cascade="all, delete-orphan")
    portfolio_items = relationship("PortfolioItem", back_populates="user", cascade="all, delete-orphan")
    work_experiences = relationship("WorkExperience", back_populates="user", cascade="all, delete-orphan")
    qr_codes = relationship("QRCode", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")

class SocialLink(Base):
    __tablename__ = "social_links"
    id = Column(String, primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    platform_name = Column(String, nullable=False)
    link_url = Column(String, nullable=False)

    user = relationship("User", back_populates="social_links")

class PortfolioItem(Base):
    __tablename__ = "portfolio_items"
    id = Column(String, primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)

    user = relationship("User", back_populates="portfolio_items")

class WorkExperience(Base):
    __tablename__ = "work_experience"
    id = Column(String, primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)

    user = relationship("User", back_populates="work_experiences")

class QRCode(Base):
    __tablename__ = "qr_codes"
    id = Column(String, primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    qr_code_url = Column(String, nullable=False)
    last_generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="qr_codes")

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(String, primary_key=True, default=generate_uuid, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)  # e.g., qr_scan, link_click
    event_data = Column(Text, nullable=True)  # JSON string with details like geo/IP, link clicked, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analytics")
