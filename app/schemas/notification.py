# app/schemas/notification.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"

class DeliveryChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"

class NotificationResponse(BaseModel):
    id: int
    alert_id: int
    alert_title: str
    alert_message: str
    alert_severity: str
    channel: DeliveryChannel
    status: DeliveryStatus
    scheduled_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    is_reminder: bool
    reminder_sequence: Optional[int]
    error_message: Optional[str]
    
    # User preference info
    is_read: bool = False
    is_snoozed: bool = False
    snoozed_until: Optional[datetime] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True