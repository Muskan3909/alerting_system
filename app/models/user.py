# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_admin = Column(Boolean, default=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="members")
    alert_preferences = relationship("UserAlertPreference", back_populates="user", cascade="all, delete-orphan")
    received_notifications = relationship("NotificationDelivery", back_populates="user", cascade="all, delete-orphan")
    created_alerts = relationship("Alert", back_populates="creator", foreign_keys="Alert.created_by")
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"