# app/models/alert.py
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class SeverityLevel(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class DeliveryType(enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"

class VisibilityType(enum.Enum):
    ORGANIZATION = "organization"
    TEAM = "team"
    USER = "user"

class AlertStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False, default=SeverityLevel.INFO)
    delivery_type = Column(Enum(DeliveryType), nullable=False, default=DeliveryType.IN_APP)
    visibility_type = Column(Enum(VisibilityType), nullable=False, default=VisibilityType.ORGANIZATION)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expiry_time = Column(DateTime(timezone=True), nullable=True)
    reminder_interval_hours = Column(Integer, default=2)
    reminders_enabled = Column(Boolean, default=True)
    
    # Visibility targeting
    target_team_ids = Column(Text, nullable=True)  # JSON array of team IDs
    target_user_ids = Column(Text, nullable=True)  # JSON array of user IDs
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="created_alerts", foreign_keys=[created_by])
    notifications = relationship("NotificationDelivery", back_populates="alert", cascade="all, delete-orphan")
    user_preferences = relationship("UserAlertPreference", back_populates="alert", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, title='{self.title}', severity='{self.severity}')>"
    
    @property
    def is_active(self):
        """Check if alert is currently active"""
        from datetime import datetime
        now = datetime.utcnow()
        
        if self.status != AlertStatus.ACTIVE:
            return False
        
        if now < self.start_time:
            return False
            
        if self.expiry_time and now > self.expiry_time:
            return False
            
        return True