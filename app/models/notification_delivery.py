# app/models/notification_delivery.py
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class DeliveryStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"

class DeliveryChannel(enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"

class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Delivery details
    channel = Column(Enum(DeliveryChannel), nullable=False, default=DeliveryChannel.IN_APP)
    status = Column(Enum(DeliveryStatus), nullable=False, default=DeliveryStatus.PENDING)
    delivery_address = Column(String(255), nullable=True)  # email address or phone number
    
    # Timing
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Metadata
    is_reminder = Column(Boolean, default=False)
    reminder_sequence = Column(Integer, nullable=True)  # 1st reminder, 2nd reminder, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    alert = relationship("Alert", back_populates="notifications")
    user = relationship("User", back_populates="received_notifications")
    
    def __repr__(self):
        return f"<NotificationDelivery(id={self.id}, alert_id={self.alert_id}, user_id={self.user_id}, status='{self.status}')>"