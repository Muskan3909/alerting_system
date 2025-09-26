from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict
from app.services.notification_service import NotificationService
from app.models.user import User
from .dependencies import get_current_user, get_current_admin_user, get_notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[Dict])
async def get_user_notifications(
    include_read: bool = Query(True, description="Include read notifications"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max number of records to return"),
    notification_service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for current user"""
    notifications = notification_service.get_user_notifications(
        user_id=current_user.id,
        include_read=include_read,
        skip=skip,
        limit=limit
    )
    return notifications

@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    notification_service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read"""
    success = notification_service.mark_notification_as_read(notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to mark notification as read. Notification may not exist or not belong to you."
        )
    return {"message": "Notification marked as read"}

@router.get("/unread", response_model=List[Dict])
async def get_unread_notifications(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max number of records to return"),
    notification_service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """Get only unread notifications for current user"""
    notifications = notification_service.get_user_notifications(
        user_id=current_user.id,
        include_read=False,
        skip=skip,
        limit=limit
    )
    return notifications