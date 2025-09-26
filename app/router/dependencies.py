# app/routers/dependencies.py
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.user_service import UserService
from app.models.user import User

# Simple authentication dependency (MVP - just user ID in header)
async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Simple authentication for MVP
    In production, this would validate JWT tokens
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header required (X-User-Id)"
        )
    
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )
    
    user_service = UserService(db)
    user = user_service.get_by_id(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

# Admin user dependency
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# Service dependencies
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Get UserService instance"""
    from app.services.user_service import UserService
    return UserService(db)

def get_team_service(db: Session = Depends(get_db)):
    """Get TeamService instance"""
    from app.services.team_service import TeamService
    return TeamService(db)

def get_alert_service(db: Session = Depends(get_db)):
    """Get AlertService instance"""
    from app.services.alert_service import AlertService
    return AlertService(db)

def get_notification_service(db: Session = Depends(get_db)):
    """Get NotificationService instance"""
    from app.services.notification_service import NotificationService
    return NotificationService(db)

def get_analytics_service(db: Session = Depends(get_db)):
    """Get AnalyticsService instance"""
    from app.services.analytics_service import AnalyticsService
    return AnalyticsService(db)