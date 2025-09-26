# app/services/alert_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import json
from app.models.alert import Alert, SeverityLevel, VisibilityType, AlertStatus
from app.models.user import User
from app.models.team import Team
from app.models.user_alert_preference import UserAlertPreference
from app.schemas.alert import AlertCreate, AlertUpdate
from .base_service import BaseService

class AlertService(BaseService[Alert, AlertCreate, AlertUpdate]):
    """
    Service class for Alert operations
    Handles alert creation, targeting, and lifecycle management
    """
    
    def __init__(self, db: Session):
        super().__init__(db, Alert)
    
    def create_alert(self, alert_data: AlertCreate, created_by: int) -> Alert:
        """Create a new alert with proper targeting and validation"""
        # Validate targeting based on visibility type
        self._validate_alert_targeting(alert_data)
        
        # Create alert data dict
        alert_dict = alert_data.model_dump()
        alert_dict['created_by'] = created_by
        
        # Convert target lists to JSON strings
        if alert_dict.get('target_team_ids'):
            alert_dict['target_team_ids'] = json.dumps(alert_dict['target_team_ids'])
        if alert_dict.get('target_user_ids'):
            alert_dict['target_user_ids'] = json.dumps(alert_dict['target_user_ids'])
        
        # Set default start time if not provided
        if not alert_dict.get('start_time'):
            alert_dict['start_time'] = datetime.utcnow()
        
        # Create the alert
        db_alert = Alert(**alert_dict)
        self.db.add(db_alert)
        self.db.commit()
        self.db.refresh(db_alert)
        
        # Create initial user alert preferences for all target users
        self._create_user_preferences_for_alert(db_alert)
        
        return db_alert
    
    def update_alert(self, alert_id: int, alert_data: AlertUpdate) -> Optional[Alert]:
        """Update alert with validation"""
        alert = self.get_by_id(alert_id)
        if not alert:
            return None
        
        # Validate targeting if visibility changed
        if alert_data.visibility_type:
            self._validate_alert_targeting(alert_data)
        
        # Convert target lists to JSON strings
        update_dict = alert_data.model_dump(exclude_unset=True)
        if 'target_team_ids' in update_dict and update_dict['target_team_ids'] is not None:
            update_dict['target_team_ids'] = json.dumps(update_dict['target_team_ids'])
        if 'target_user_ids' in update_dict and update_dict['target_user_ids'] is not None:
            update_dict['target_user_ids'] = json.dumps(update_dict['target_user_ids'])
        
        # Update fields
        for field, value in update_dict.items():
            setattr(alert, field, value)
        
        self.db.commit()
        self.db.refresh(alert)
        
        # If targeting changed, update user preferences
        if any(field in update_dict for field in ['visibility_type', 'target_team_ids', 'target_user_ids']):
            self._update_user_preferences_for_alert(alert)
        
        return alert
    
    def get_alerts_for_user(self, user_id: int, include_read: bool = True, 
                           skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all alerts that should be visible to a specific user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        query = self.db.query(Alert).filter(Alert.status == AlertStatus.ACTIVE)
        
        # Build visibility filter
        visibility_filters = []
        
        # Organization-wide alerts
        visibility_filters.append(Alert.visibility_type == VisibilityType.ORGANIZATION)
        
        # Team-specific alerts
        if user.team_id:
            visibility_filters.append(and_(
                Alert.visibility_type == VisibilityType.TEAM,
                Alert.target_team_ids.like(f'%{user.team_id}%')
            ))
        
        # User-specific alerts
        visibility_filters.append(and_(
            Alert.visibility_type == VisibilityType.USER,
            Alert.target_user_ids.like(f'%{user_id}%')
        ))
        
        query = query.filter(or_(*visibility_filters))
        
        # Join with user preferences to get read/snooze status
        query = (query.outerjoin(UserAlertPreference, and_(
                    Alert.id == UserAlertPreference.alert_id,
                    UserAlertPreference.user_id == user_id
                ))
                .add_columns(
                    UserAlertPreference.is_read,
                    UserAlertPreference.is_snoozed,
                    UserAlertPreference.snoozed_until,
                    UserAlertPreference.read_at
                ))
        
        # Filter by read status if requested
        if not include_read:
            query = query.filter(or_(
                UserAlertPreference.is_read == False,
                UserAlertPreference.is_read.is_(None)
            ))
        
        results = query.offset(skip).limit(limit).all()
        
        # Format results
        alerts = []
        for row in results:
            alert = row[0]  # Alert object
            is_read = row[1] if row[1] is not None else False
            is_snoozed = row[2] if row[2] is not None else False
            snoozed_until = row[3]
            read_at = row[4]
            
            alert_dict = {
                'id': alert.id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity.value,
                'start_time': alert.start_time,
                'expiry_time': alert.expiry_time,
                'is_active': alert.is_active,
                'created_at': alert.created_at,
                'is_read': is_read,
                'is_snoozed': is_snoozed,
                'snoozed_until': snoozed_until,
                'read_at': read_at
            }
            alerts.append(alert_dict)
        
        return alerts
    
    def mark_alert_as_read(self, alert_id: int, user_id: int) -> bool:
        """Mark an alert as read for a specific user"""
        # Get or create user alert preference
        preference = self._get_or_create_user_preference(alert_id, user_id)
        if preference:
            preference.mark_as_read()
            self.db.commit()
            return True
        return False
    
    def snooze_alert_for_user(self, alert_id: int, user_id: int) -> bool:
        """Snooze an alert for a specific user until end of day"""
        preference = self._get_or_create_user_preference(alert_id, user_id)
        if preference:
            preference.snooze_for_day()
            self.db.commit()
            return True
        return False
    
    def get_alerts_by_filters(self, severity: Optional[SeverityLevel] = None,
                            status: Optional[AlertStatus] = None,
                            created_by: Optional[int] = None,
                            skip: int = 0, limit: int = 100) -> List[Alert]:
        """Get alerts with optional filters"""
        query = self.db.query(Alert)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        if status:
            query = query.filter(Alert.status == status)
        if created_by:
            query = query.filter(Alert.created_by == created_by)
        
        return query.offset(skip).limit(limit).all()
    
    def get_alerts_requiring_reminders(self) -> List[Dict]:
        """Get alerts that need to send reminders to users"""
        now = datetime.utcnow()
        
        # Get active alerts with reminders enabled
        active_alerts = (self.db.query(Alert)
                        .filter(and_(
                            Alert.status == AlertStatus.ACTIVE,
                            Alert.reminders_enabled == True,
                            Alert.start_time <= now,
                            or_(Alert.expiry_time.is_(None), Alert.expiry_time > now)
                        ))
                        .all())
        
        reminder_data = []
        for alert in active_alerts:
            # Get users who need reminders for this alert
            users_needing_reminders = (self.db.query(UserAlertPreference)
                                     .filter(and_(
                                         UserAlertPreference.alert_id == alert.id,
                                         UserAlertPreference.is_read == False,
                                         or_(
                                             UserAlertPreference.is_snoozed == False,
                                             UserAlertPreference.snoozed_until < now
                                         ),
                                         or_(
                                             UserAlertPreference.last_reminded_at.is_(None),
                                             UserAlertPreference.last_reminded_at < 
                                             (now - timedelta(hours=alert.reminder_interval_hours))
                                         )
                                     ))
                                     .all())
            
            if users_needing_reminders:
                reminder_data.append({
                    'alert': alert,
                    'users': users_needing_reminders
                })
        
        return reminder_data
    
    def archive_alert(self, alert_id: int) -> bool:
        """Archive an alert"""
        alert = self.get_by_id(alert_id)
        if alert:
            alert.status = AlertStatus.ARCHIVED
            self.db.commit()
            return True
        return False
    
    def _validate_alert_targeting(self, alert_data):
        """Validate alert targeting based on visibility type"""
        if alert_data.visibility_type == VisibilityType.TEAM:
            if not alert_data.target_team_ids:
                raise ValueError("Team IDs required for team-specific alerts")
            # Validate team IDs exist
            for team_id in alert_data.target_team_ids:
                if not self.db.query(Team).filter(Team.id == team_id).first():
                    raise ValueError(f"Team with ID {team_id} does not exist")
        
        elif alert_data.visibility_type == VisibilityType.USER:
            if not alert_data.target_user_ids:
                raise ValueError("User IDs required for user-specific alerts")
            # Validate user IDs exist
            for user_id in alert_data.target_user_ids:
                if not self.db.query(User).filter(User.id == user_id).first():
                    raise ValueError(f"User with ID {user_id} does not exist")
    
    def _create_user_preferences_for_alert(self, alert: Alert):
        """Create user alert preferences for all target users of an alert"""
        target_users = self._get_target_users_for_alert(alert)
        
        for user in target_users:
            # Check if preference already exists
            existing = (self.db.query(UserAlertPreference)
                       .filter(and_(
                           UserAlertPreference.user_id == user.id,
                           UserAlertPreference.alert_id == alert.id
                       ))
                       .first())
            
            if not existing:
                preference = UserAlertPreference(
                    user_id=user.id,
                    alert_id=alert.id
                )
                self.db.add(preference)
        
        self.db.commit()
    
    def _update_user_preferences_for_alert(self, alert: Alert):
        """Update user preferences when alert targeting changes"""
        # Delete existing preferences
        self.db.query(UserAlertPreference).filter(
            UserAlertPreference.alert_id == alert.id
        ).delete()
        
        # Create new preferences
        self._create_user_preferences_for_alert(alert)
    
    def _get_target_users_for_alert(self, alert: Alert) -> List[User]:
        """Get all users who should receive this alert"""
        if alert.visibility_type == VisibilityType.ORGANIZATION:
            return self.db.query(User).filter(User.is_active == True).all()
        
        elif alert.visibility_type == VisibilityType.TEAM:
            team_ids = json.loads(alert.target_team_ids) if alert.target_team_ids else []
            return (self.db.query(User)
                   .filter(and_(
                       User.is_active == True,
                       User.team_id.in_(team_ids)
                   ))
                   .all())
        
        elif alert.visibility_type == VisibilityType.USER:
            user_ids = json.loads(alert.target_user_ids) if alert.target_user_ids else []
            return (self.db.query(User)
                   .filter(and_(
                       User.is_active == True,
                       User.id.in_(user_ids)
                   ))
                   .all())
        
        return []
    
    def _get_or_create_user_preference(self, alert_id: int, user_id: int) -> Optional[UserAlertPreference]:
        """Get or create user alert preference"""
        preference = (self.db.query(UserAlertPreference)
                     .filter(and_(
                         UserAlertPreference.alert_id == alert_id,
                         UserAlertPreference.user_id == user_id
                     ))
                     .first())
        
        if not preference:
            # Verify alert and user exist
            alert = self.get_by_id(alert_id)
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if alert and user:
                preference = UserAlertPreference(
                    alert_id=alert_id,
                    user_id=user_id
                )
                self.db.add(preference)
                self.db.commit()
        
        return preference