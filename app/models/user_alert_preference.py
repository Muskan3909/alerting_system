# app/models/user_alert_preference.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime, date

class UserAlertPreference(Base):
    __tablename__ = "user_alert_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    
    # Read/Unread status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Snooze functionality
    is_snoozed = Column(Boolean, default=False)
    snoozed_at = Column(DateTime(timezone=True), nullable=True)
    snoozed_until = Column(DateTime(timezone=True), nullable=True)  # End of day snooze
    snooze_count = Column(Integer, default=0)  # Track how many times user snoozed
    
    # Last interaction tracking
    last_reminded_at = Column(DateTime(timezone=True), nullable=True)
    reminder_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="alert_preferences")
    alert = relationship("Alert", back_populates="user_preferences")
    
    # Ensure one preference record per user per alert
    __table_args__ = (
        UniqueConstraint('user_id', 'alert_id', name='_user_alert_preference_uc'),
    )
    
    def __repr__(self):
        return f"<UserAlertPreference(user_id={self.user_id}, alert_id={self.alert_id}, is_read={self.is_read}, is_snoozed={self.is_snoozed})>"
    
    @property
    def should_receive_reminder(self):
        """Check if user should receive reminder for this alert"""
        from datetime import datetime, timedelta
        
        # If snoozed, check if snooze period has expired
        if self.is_snoozed:
            now = datetime.utcnow()
            if self.snoozed_until and now < self.snoozed_until:
                return False
            else:
                # Snooze period expired, reset snooze
                self.is_snoozed = False
                self.snoozed_until = None
        
        # If already read, don't send reminders
        if self.is_read:
            return False
        
        # Check if enough time has passed since last reminder
        if self.last_reminded_at:
            time_since_last = datetime.utcnow() - self.last_reminded_at
            # Get reminder interval from alert (default 2 hours)
            interval_hours = getattr(self.alert, 'reminder_interval_hours', 2)
            if time_since_last.total_seconds() < (interval_hours * 3600):
                return False
        
        return True
    
    def mark_as_read(self):
        """Mark alert as read for this user"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def snooze_for_day(self):
        """Snooze alert until end of current day"""
        from datetime import datetime, time
        
        now = datetime.utcnow()
        # Snooze until 11:59 PM of current day
        end_of_day = datetime.combine(now.date(), time(23, 59, 59))
        
        self.is_snoozed = True
        self.snoozed_at = now
        self.snoozed_until = end_of_day
        self.snooze_count += 1
        self.updated_at = now