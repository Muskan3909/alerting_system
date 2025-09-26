# app/schemas/alert.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums (matching the database models)
class SeverityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class DeliveryType(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"

class VisibilityType(str, Enum):
    ORGANIZATION = "organization"
    TEAM = "team"
    USER = "user"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"

# Base Alert Schema
class AlertBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    severity: SeverityLevel = SeverityLevel.INFO
    delivery_type: DeliveryType = DeliveryType.IN_APP
    visibility_type: VisibilityType = VisibilityType.ORGANIZATION
    reminder_interval_hours: int = Field(default=2, ge=1, le=168)  # 1 hour to 1 week
    reminders_enabled: bool = True

class AlertCreate(AlertBase):
    start_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    target_team_ids: Optional[List[int]] = None
    target_user_ids: Optional[List[int]] = None

class AlertUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1)
    severity: Optional[SeverityLevel] = None
    delivery_type: Optional[DeliveryType] = None
    visibility_type: Optional[VisibilityType] = None
    status: Optional[AlertStatus] = None
    start_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    reminder_interval_hours: Optional[int] = Field(None, ge=1, le=168)
    reminders_enabled: Optional[bool] = None
    target_team_ids: Optional[List[int]] = None
    target_user_ids: Optional[List[int]] = None

class AlertResponse(AlertBase):
    id: int
    status: AlertStatus
    start_time: datetime
    expiry_time: Optional[datetime]
    target_team_ids: Optional[List[int]]
    target_user_ids: Optional[List[int]]
    created_by: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    # Stats
    total_recipients: Optional[int] = 0
    read_count: Optional[int] = 0
    snoozed_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# User-specific alert actions
class AlertActionRequest(BaseModel):
    alert_id: int

class SnoozeAlertRequest(AlertActionRequest):
    pass

class MarkReadRequest(AlertActionRequest):
    pass