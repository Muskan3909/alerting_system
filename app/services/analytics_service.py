# app/services/analytics_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, List
from datetime import datetime, timedelta
from app.models.alert import Alert, SeverityLevel, AlertStatus
from app.models.user import User
from app.models.team import Team
from app.models.notification_delivery import NotificationDelivery, DeliveryStatus
from app.models.user_alert_preference import UserAlertPreference
from app.schemas.analytics import (
    AnalyticsResponse, SeverityBreakdown, AlertStatusBreakdown,
    DeliveryStats, SnoozeStats, TopAlert
)

class AnalyticsService:
    """
    Service for generating analytics and metrics
    Provides insights into alert performance and user engagement
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_analytics_report(self) -> AnalyticsResponse:
        """Generate comprehensive analytics report"""
        return AnalyticsResponse(
            # Overview metrics
            total_alerts_created=self._get_total_alerts_created(),
            active_alerts=self._get_active_alerts_count(),
            total_users=self._get_total_users_count(),
            total_teams=self._get_total_teams_count(),
            
            # Alert breakdown
            alerts_by_severity=self._get_alerts_by_severity(),
            alerts_by_status=self._get_alerts_by_status(),
            
            # Delivery & engagement
            delivery_stats=self._get_delivery_stats(),
            snooze_stats=self._get_snooze_stats(),
            
            # Top performing alerts
            most_read_alerts=self._get_most_read_alerts(),
            most_snoozed_alerts=self._get_most_snoozed_alerts(),
            
            # Time-based stats
            alerts_created_today=self._get_alerts_created_today(),
            alerts_created_this_week=self._get_alerts_created_this_week(),
            alerts_created_this_month=self._get_alerts_created_this_month(),
            
            # Response rates
            overall_read_rate=self._get_overall_read_rate(),
            overall_snooze_rate=self._get_overall_snooze_rate(),
            
            generated_at=datetime.utcnow()
        )
    
    def get_alert_performance_metrics(self, alert_id: int) -> Dict:
        """Get detailed performance metrics for a specific alert"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return {}
        
        # Basic stats
        total_recipients = (self.db.query(UserAlertPreference)
                          .filter(UserAlertPreference.alert_id == alert_id)
                          .count())
        
        read_count = (self.db.query(UserAlertPreference)
                     .filter(and_(
                         UserAlertPreference.alert_id == alert_id,
                         UserAlertPreference.is_read == True
                     ))
                     .count())
        
        snoozed_count = (self.db.query(UserAlertPreference)
                        .filter(and_(
                            UserAlertPreference.alert_id == alert_id,
                            UserAlertPreference.is_snoozed == True
                        ))
                        .count())
        
        # Delivery stats
        total_deliveries = (self.db.query(NotificationDelivery)
                           .filter(NotificationDelivery.alert_id == alert_id)
                           .count())
        
        successful_deliveries = (self.db.query(NotificationDelivery)
                                .filter(and_(
                                    NotificationDelivery.alert_id == alert_id,
                                    NotificationDelivery.status.in_([
                                        DeliveryStatus.DELIVERED,
                                        DeliveryStatus.READ
                                    ])
                                ))
                                .count())
        
        # Reminder stats
        total_reminders = (self.db.query(NotificationDelivery)
                          .filter(and_(
                              NotificationDelivery.alert_id == alert_id,
                              NotificationDelivery.is_reminder == True
                          ))
                          .count())
        
        return {
            'alert_id': alert_id,
            'alert_title': alert.title,
            'alert_severity': alert.severity.value,
            'created_at': alert.created_at,
            'total_recipients': total_recipients,
            'read_count': read_count,
            'snoozed_count': snoozed_count,
            'read_rate': (read_count / total_recipients * 100) if total_recipients > 0 else 0,
            'snooze_rate': (snoozed_count / total_recipients * 100) if total_recipients > 0 else 0,
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'delivery_success_rate': (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0,
            'total_reminders': total_reminders,
            'average_reminders_per_user': (total_reminders / total_recipients) if total_recipients > 0 else 0
        }
    
    def get_user_engagement_metrics(self, user_id: int) -> Dict:
        """Get engagement metrics for a specific user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Alert interaction stats
        total_alerts_received = (self.db.query(UserAlertPreference)
                               .filter(UserAlertPreference.user_id == user_id)
                               .count())
        
        alerts_read = (self.db.query(UserAlertPreference)
                      .filter(and_(
                          UserAlertPreference.user_id == user_id,
                          UserAlertPreference.is_read == True
                      ))
                      .count())
        
        alerts_snoozed = (self.db.query(UserAlertPreference)
                         .filter(UserAlertPreference.user_id == user_id)
                         .with_entities(func.sum(UserAlertPreference.snooze_count))
                         .scalar()) or 0
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_alerts = (self.db.query(UserAlertPreference)
                        .join(Alert, UserAlertPreference.alert_id == Alert.id)
                        .filter(and_(
                            UserAlertPreference.user_id == user_id,
                            Alert.created_at >= thirty_days_ago
                        ))
                        .count())
        
        recent_reads = (self.db.query(UserAlertPreference)
                       .filter(and_(
                           UserAlertPreference.user_id == user_id,
                           UserAlertPreference.read_at >= thirty_days_ago
                       ))
                       .count()) if thirty_days_ago else 0
        
        return {
            'user_id': user_id,
            'user_name': user.name,
            'user_email': user.email,
            'team_id': user.team_id,
            'total_alerts_received': total_alerts_received,
            'alerts_read': alerts_read,
            'alerts_snoozed': alerts_snoozed,
            'read_rate': (alerts_read / total_alerts_received * 100) if total_alerts_received > 0 else 0,
            'average_snoozes_per_alert': (alerts_snoozed / total_alerts_received) if total_alerts_received > 0 else 0,
            'recent_alerts_30d': recent_alerts,
            'recent_reads_30d': recent_reads,
            'recent_read_rate': (recent_reads / recent_alerts * 100) if recent_alerts > 0 else 0
        }
    
    def get_team_analytics(self, team_id: int) -> Dict:
        """Get analytics for a specific team"""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {}
        
        # Team members
        team_members = (self.db.query(User)
                       .filter(and_(User.team_id == team_id, User.is_active == True))
                       .all())
        
        member_ids = [member.id for member in team_members]
        
        if not member_ids:
            return {
                'team_id': team_id,
                'team_name': team.name,
                'member_count': 0,
                'total_alerts_received': 0,
                'team_read_rate': 0,
                'team_snooze_rate': 0
            }
        
        # Aggregate team stats
        total_alerts = (self.db.query(UserAlertPreference)
                       .filter(UserAlertPreference.user_id.in_(member_ids))
                       .count())
        
        total_reads = (self.db.query(UserAlertPreference)
                      .filter(and_(
                          UserAlertPreference.user_id.in_(member_ids),
                          UserAlertPreference.is_read == True
                      ))
                      .count())
        
        total_snoozes = (self.db.query(UserAlertPreference)
                        .filter(UserAlertPreference.user_id.in_(member_ids))
                        .with_entities(func.sum(UserAlertPreference.snooze_count))
                        .scalar()) or 0
        
        return {
            'team_id': team_id,
            'team_name': team.name,
            'member_count': len(team_members),
            'total_alerts_received': total_alerts,
            'total_reads': total_reads,
            'total_snoozes': total_snoozes,
            'team_read_rate': (total_reads / total_alerts * 100) if total_alerts > 0 else 0,
            'team_snooze_rate': (total_snoozes / total_alerts * 100) if total_alerts > 0 else 0,
            'average_alerts_per_member': (total_alerts / len(team_members)) if team_members else 0,
            'average_reads_per_member': (total_reads / len(team_members)) if team_members else 0
        }
    
    # Private helper methods
    def _get_total_alerts_created(self) -> int:
        return self.db.query(Alert).count()
    
    def _get_active_alerts_count(self) -> int:
        return self.db.query(Alert).filter(Alert.status == AlertStatus.ACTIVE).count()
    
    def _get_total_users_count(self) -> int:
        return self.db.query(User).filter(User.is_active == True).count()
    
    def _get_total_teams_count(self) -> int:
        return self.db.query(Team).filter(Team.is_active == True).count()
    
    def _get_alerts_by_severity(self) -> SeverityBreakdown:
        severity_counts = (self.db.query(Alert.severity, func.count(Alert.id))
                          .group_by(Alert.severity)
                          .all())
        
        breakdown = SeverityBreakdown()
        for severity, count in severity_counts:
            if severity == SeverityLevel.INFO:
                breakdown.info = count
            elif severity == SeverityLevel.WARNING:
                breakdown.warning = count
            elif severity == SeverityLevel.CRITICAL:
                breakdown.critical = count
        
        return breakdown
    
    def _get_alerts_by_status(self) -> AlertStatusBreakdown:
        status_counts = (self.db.query(Alert.status, func.count(Alert.id))
                        .group_by(Alert.status)
                        .all())
        
        breakdown = AlertStatusBreakdown()
        for status, count in status_counts:
            if status == AlertStatus.ACTIVE:
                breakdown.active = count
            elif status == AlertStatus.EXPIRED:
                breakdown.expired = count
            elif status == AlertStatus.ARCHIVED:
                breakdown.archived = count
        
        return breakdown
    
    def _get_delivery_stats(self) -> DeliveryStats:
        total_sent = self.db.query(NotificationDelivery).filter(
            NotificationDelivery.status.in_([
                DeliveryStatus.SENT, DeliveryStatus.DELIVERED, DeliveryStatus.READ
            ])
        ).count()
        
        total_delivered = self.db.query(NotificationDelivery).filter(
            NotificationDelivery.status.in_([DeliveryStatus.DELIVERED, DeliveryStatus.READ])
        ).count()
        
        total_read = self.db.query(NotificationDelivery).filter(
            NotificationDelivery.status == DeliveryStatus.READ
        ).count()
        
        total_failed = self.db.query(NotificationDelivery).filter(
            NotificationDelivery.status == DeliveryStatus.FAILED
        ).count()
        
        return DeliveryStats(
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_read=total_read,
            total_failed=total_failed,
            delivery_rate=(total_delivered / total_sent * 100) if total_sent > 0 else 0,
            read_rate=(total_read / total_delivered * 100) if total_delivered > 0 else 0
        )
    
    def _get_snooze_stats(self) -> SnoozeStats:
        total_snoozed = (self.db.query(UserAlertPreference)
                        .with_entities(func.sum(UserAlertPreference.snooze_count))
                        .scalar()) or 0
        
        active_snoozes = (self.db.query(UserAlertPreference)
                         .filter(and_(
                             UserAlertPreference.is_snoozed == True,
                             UserAlertPreference.snoozed_until > datetime.utcnow()
                         ))
                         .count())
        
        total_alerts = self.db.query(Alert).count()
        
        return SnoozeStats(
            total_snoozed=total_snoozed,
            active_snoozes=active_snoozes,
            average_snoozes_per_alert=(total_snoozed / total_alerts) if total_alerts > 0 else 0
        )
    
    def _get_most_read_alerts(self, limit: int = 5) -> List[TopAlert]:
        results = (self.db.query(
                    Alert.id,
                    Alert.title,
                    Alert.severity,
                    Alert.created_at,
                    func.count(UserAlertPreference.id).label('recipients'),
                    func.sum(func.cast(UserAlertPreference.is_read, func.Integer)).label('read_count'),
                    func.sum(UserAlertPreference.snooze_count).label('snooze_count')
                )
                .join(UserAlertPreference, Alert.id == UserAlertPreference.alert_id)
                .group_by(Alert.id)
                .order_by(func.sum(func.cast(UserAlertPreference.is_read, func.Integer)).desc())
                .limit(limit)
                .all())
        
        return [
            TopAlert(
                id=row.id,
                title=row.title,
                severity=row.severity.value,
                recipients=row.recipients,
                read_count=row.read_count or 0,
                snooze_count=row.snooze_count or 0,
                created_at=row.created_at
            ) for row in results
        ]
    
    def _get_most_snoozed_alerts(self, limit: int = 5) -> List[TopAlert]:
        results = (self.db.query(
                    Alert.id,
                    Alert.title,
                    Alert.severity,
                    Alert.created_at,
                    func.count(UserAlertPreference.id).label('recipients'),
                    func.sum(func.cast(UserAlertPreference.is_read, func.Integer)).label('read_count'),
                    func.sum(UserAlertPreference.snooze_count).label('snooze_count')
                )
                .join(UserAlertPreference, Alert.id == UserAlertPreference.alert_id)
                .group_by(Alert.id)
                .order_by(func.sum(UserAlertPreference.snooze_count).desc())
                .limit(limit)
                .all())
        
        return [
            TopAlert(
                id=row.id,
                title=row.title,
                severity=row.severity.value,
                recipients=row.recipients,
                read_count=row.read_count or 0,
                snooze_count=row.snooze_count or 0,
                created_at=row.created_at
            ) for row in results
        ]
    
    def _get_alerts_created_today(self) -> int:
        today = datetime.utcnow().date()
        return (self.db.query(Alert)
                .filter(func.date(Alert.created_at) == today)
                .count())
    
    def _get_alerts_created_this_week(self) -> int:
        week_ago = datetime.utcnow() - timedelta(days=7)
        return (self.db.query(Alert)
                .filter(Alert.created_at >= week_ago)
                .count())
    
    def _get_alerts_created_this_month(self) -> int:
        month_ago = datetime.utcnow() - timedelta(days=30)
        return (self.db.query(Alert)
                .filter(Alert.created_at >= month_ago)
                .count())
    
    def _get_overall_read_rate(self) -> float:
        total_preferences = self.db.query(UserAlertPreference).count()
        if total_preferences == 0:
            return 0.0
        
        read_preferences = (self.db.query(UserAlertPreference)
                           .filter(UserAlertPreference.is_read == True)
                           .count())
        
        return (read_preferences / total_preferences) * 100
    
    def _get_overall_snooze_rate(self) -> float:
        total_preferences = self.db.query(UserAlertPreference).count()
        if total_preferences == 0:
            return 0.0
        
        total_snoozes = (self.db.query(UserAlertPreference)
                        .with_entities(func.sum(UserAlertPreference.snooze_count))
                        .scalar()) or 0
        
        return (total_snoozes / total_preferences) * 100