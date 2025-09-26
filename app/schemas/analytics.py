# app/schemas/analytics.py
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class SeverityBreakdown(BaseModel):
    info: int = 0
    warning: int = 0
    critical: int = 0

class AlertStatusBreakdown(BaseModel):
    active: int = 0
    expired: int = 0
    archived: int = 0

class DeliveryStats(BaseModel):
    total_sent: int = 0
    total_delivered: int = 0
    total_read: int = 0
    total_failed: int = 0
    delivery_rate: float = 0.0  # delivered / sent
    read_rate: float = 0.0     # read / delivered

class SnoozeStats(BaseModel):
    total_snoozed: int = 0
    active_snoozes: int = 0
    average_snoozes_per_alert: float = 0.0

class TopAlert(BaseModel):
    id: int
    title: str
    severity: str
    recipients: int
    read_count: int
    snooze_count: int
    created_at: datetime

class AnalyticsResponse(BaseModel):
    # Overview metrics
    total_alerts_created: int = 0
    active_alerts: int = 0
    total_users: int = 0
    total_teams: int = 0
    
    # Alert breakdown
    alerts_by_severity: SeverityBreakdown
    alerts_by_status: AlertStatusBreakdown
    
    # Delivery & engagement
    delivery_stats: DeliveryStats
    snooze_stats: SnoozeStats
    
    # Top performing alerts
    most_read_alerts: List[TopAlert] = []
    most_snoozed_alerts: List[TopAlert] = []
    
    # Time-based stats
    alerts_created_today: int = 0
    alerts_created_this_week: int = 0
    alerts_created_this_month: int = 0
    
    # Response rates
    overall_read_rate: float = 0.0
    overall_snooze_rate: float = 0.0
    
    generated_at: datetime