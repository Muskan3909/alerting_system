# app/routers/alerts.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.schemas.alert import (
    AlertCreate, AlertUpdate, AlertResponse, AlertListResponse,
    SeverityLevel, AlertStatus, MarkReadRequest, SnoozeAlertRequest
)
from app.services.alert_service import AlertService
from app.models.user import User
from .dependencies import get_current_user, get_current_admin_user, get_alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Admin endpoints
@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new alert (Admin only)"""
    try:
        alert = alert_service.create_alert(alert_data, current_user.id)
        
        # Convert to response format
        alert_dict = alert.__dict__.copy()
        alert_dict['is_active'] = alert.is_active
        alert_dict['target_team_ids'] = eval(alert.target_team_ids) if alert.target_team_ids else None
        alert_dict['target_user_ids'] = eval(alert.target_user_ids) if alert.target_user_ids else None
        alert_dict['total_recipients'] = 0  # Will be calculated by service
        alert_dict['read_count'] = 0
        alert_dict['snoozed_count'] = 0
        
        return alert_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/admin", response_model=List[AlertResponse])
async def list_all_alerts_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[SeverityLevel] = Query(None),
    status: Optional[AlertStatus] = Query(None),
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_admin_user)
):
    """List all alerts with admin filters"""
    alerts = alert_service.get_alerts_by_filters(
        severity=severity,
        status=status,
        created_by=None,
        skip=skip,
        limit=limit
    )
    
    # Convert to response format
    response_alerts = []
    for alert in alerts:
        alert_dict = alert.__dict__.copy()
        alert_dict['is_active'] = alert.is_active
        alert_dict['target_team_ids'] = eval(alert.target_team_ids) if alert.target_team_ids else None
        alert_dict['target_user_ids'] = eval(alert.target_user_ids) if alert.target_user_ids else None
        alert_dict['total_recipients'] = 0  # TODO: Calculate from service
        alert_dict['read_count'] = 0
        alert_dict['snoozed_count'] = 0
        response_alerts.append(alert_dict)
    
    return response_alerts

@router.get("/admin/{alert_id}", response_model=AlertResponse)
async def get_alert_admin(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Get alert by ID (Admin only)"""
    alert = alert_service.get_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Convert to response format
    alert_dict = alert.__dict__.copy()
    alert_dict['is_active'] = alert.is_active
    alert_dict['target_team_ids'] = eval(alert.target_team_ids) if alert.target_team_ids else None
    alert_dict['target_user_ids'] = eval(alert.target_user_ids) if alert.target_user_ids else None
    alert_dict['total_recipients'] = 0
    alert_dict['read_count'] = 0
    alert_dict['snoozed_count'] = 0
    
    return alert_dict

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Update alert (Admin only)"""
    try:
        updated_alert = alert_service.update_alert(alert_id, alert_data)
        if not updated_alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Convert to response format
        alert_dict = updated_alert.__dict__.copy()
        alert_dict['is_active'] = updated_alert.is_active
        alert_dict['target_team_ids'] = eval(updated_alert.target_team_ids) if updated_alert.target_team_ids else None
        alert_dict['target_user_ids'] = eval(updated_alert.target_user_ids) if updated_alert.target_user_ids else None
        alert_dict['total_recipients'] = 0
        alert_dict['read_count'] = 0
        alert_dict['snoozed_count'] = 0
        
        return alert_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{alert_id}")
async def archive_alert(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Archive alert (Admin only)"""
    success = alert_service.archive_alert(alert_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    return {"message": "Alert archived successfully"}

# User endpoints
@router.get("/", response_model=List[dict])
async def get_user_alerts(
    include_read: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_user)
):
    """Get alerts visible to current user"""
    alerts = alert_service.get_alerts_for_user(
        user_id=current_user.id,
        include_read=include_read,
        skip=skip,
        limit=limit
    )
    return alerts

@router.post("/mark-read")
async def mark_alert_as_read(
    request: MarkReadRequest,
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_user)
):
    """Mark an alert as read for current user"""
    success = alert_service.mark_alert_as_read(request.alert_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to mark alert as read. Alert may not exist or not be visible to you."
        )
    return {"message": "Alert marked as read"}

@router.post("/snooze")
async def snooze_alert(
    request: SnoozeAlertRequest,
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_user)
):
    """Snooze an alert for current user until end of day"""
    success = alert_service.snooze_alert_for_user(request.alert_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to snooze alert. Alert may not exist or not be visible to you."
        )
    return {"message": "Alert snoozed until end of day"}

@router.get("/unread")
async def get_unread_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_user)
):
    """Get only unread alerts for current user"""
    alerts = alert_service.get_alerts_for_user(
        user_id=current_user.id,
        include_read=False,
        skip=skip,
        limit=limit
    )
    return alerts

@router.get("/count")
async def get_alert_counts(
    alert_service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_user)
):
    """Get alert counts for current user"""
    all_alerts = alert_service.get_alerts_for_user(current_user.id, include_read=True)
    unread_alerts = alert_service.get_alerts_for_user(current_user.id, include_read=False)
    
    snoozed_count = sum(1 for alert in all_alerts if alert.get('is_snoozed', False))
    
    return {
        "total_alerts": len(all_alerts),
        "unread_alerts": len(unread_alerts),
        "read_alerts": len(all_alerts) - len(unread_alerts),
        "snoozed_alerts": snoozed_count
    }