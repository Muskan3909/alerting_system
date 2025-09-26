from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import AnalyticsResponse
from app.models.user import User
from .dependencies import get_current_user, get_current_admin_user, get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_analytics_dashboard(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Get comprehensive analytics dashboard (Admin only)"""
    return analytics_service.generate_analytics_report()

@router.get("/alert/{alert_id}")
async def get_alert_performance(
    alert_id: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get performance metrics for a specific alert (Admin only)"""
    metrics = analytics_service.get_alert_performance_metrics(alert_id)
    if not metrics:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    return metrics

@router.get("/user/{user_id}")
async def get_user_engagement(
    user_id: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get engagement metrics for a specific user (Admin only)"""
    metrics = analytics_service.get_user_engagement_metrics(user_id)
    if not metrics:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return metrics

@router.get("/team/{team_id}")
async def get_team_analytics(
    team_id: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Get analytics for a specific team (Admin only)"""
    metrics = analytics_service.get_team_analytics(team_id)
    if not metrics:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return metrics

@router.get("/me")
async def get_my_engagement(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get engagement metrics for current user"""
    return analytics_service.get_user_engagement_metrics(current_user.id)
