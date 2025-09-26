# app/services/notification_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from app.models.notification_delivery import NotificationDelivery, DeliveryStatus, DeliveryChannel
from app.models.alert import Alert
from app.models.user import User
from app.models.user_alert_preference import UserAlertPreference

# Strategy Pattern for different delivery channels
class NotificationChannel(ABC):
    """Abstract base class for notification channels"""
    
    @abstractmethod
    def send_notification(self, alert: Alert, user: User, delivery_record: NotificationDelivery) -> bool:
        """Send notification through this channel"""
        pass
    
    @abstractmethod
    def get_channel_type(self) -> DeliveryChannel:
        """Get the channel type"""
        pass

class InAppChannel(NotificationChannel):
    """In-app notification channel (MVP implementation)"""
    
    def send_notification(self, alert: Alert, user: User, delivery_record: NotificationDelivery) -> bool:
        """For in-app, we just mark as sent since it's stored in database"""
        try:
            delivery_record.status = DeliveryStatus.SENT
            delivery_record.sent_at = datetime.utcnow()
            delivery_record.delivered_at = datetime.utcnow()  # In-app is instantly "delivered"
            delivery_record.status = DeliveryStatus.DELIVERED
            return True
        except Exception as e:
            delivery_record.error_message = str(e)
            return False
    
    def get_channel_type(self) -> DeliveryChannel:
        return DeliveryChannel.IN_APP

class EmailChannel(NotificationChannel):
    """Email notification channel (Future implementation)"""
    
    def send_notification(self, alert: Alert, user: User, delivery_record: NotificationDelivery) -> bool:
        """Send email notification (placeholder for future implementation)"""
        # TODO: Implement email sending logic
        # For now, just mark as failed since not implemented
        delivery_record.error_message = "Email delivery not implemented yet"
        return False
    
    def get_channel_type(self) -> DeliveryChannel:
        return DeliveryChannel.EMAIL

class SMSChannel(NotificationChannel):
    """SMS notification channel (Future implementation)"""
    
    def send_notification(self, alert: Alert, user: User, delivery_record: NotificationDelivery) -> bool:
        """Send SMS notification (placeholder for future implementation)"""
        # TODO: Implement SMS sending logic
        # For now, just mark as failed since not implemented
        delivery_record.error_message = "SMS delivery not implemented yet"
        return False
    
    def get_channel_type(self) -> DeliveryChannel:
        return DeliveryChannel.SMS

class NotificationService:
    """
    Service for managing notification delivery
    Uses Strategy pattern for different delivery channels
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.channels = {
            DeliveryChannel.IN_APP: InAppChannel(),
            DeliveryChannel.EMAIL: EmailChannel(),
            DeliveryChannel.SMS: SMSChannel()
        }
    
    def schedule_notification(self, alert: Alert, user: User, 
                            channel: DeliveryChannel = DeliveryChannel.IN_APP,
                            is_reminder: bool = False,
                            reminder_sequence: int = None) -> NotificationDelivery:
        """Schedule a notification for delivery"""
        
        # Create delivery record
        delivery = NotificationDelivery(
            alert_id=alert.id,
            user_id=user.id,
            channel=channel,
            status=DeliveryStatus.PENDING,
            scheduled_at=datetime.utcnow(),
            is_reminder=is_reminder,
            reminder_sequence=reminder_sequence,
            delivery_address=self._get_delivery_address(user, channel)
        )
        
        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)
        
        return delivery
    
    def send_pending_notifications(self) -> Dict[str, int]:
        """Send all pending notifications"""
        pending_notifications = (self.db.query(NotificationDelivery)
                               .filter(NotificationDelivery.status == DeliveryStatus.PENDING)
                               .all())
        
        results = {
            'sent': 0,
            'failed': 0,
            'total': len(pending_notifications)
        }
        
        for delivery in pending_notifications:
            if self._send_notification(delivery):
                results['sent'] += 1
            else:
                results['failed'] += 1
        
        self.db.commit()
        return results
    
    def send_notification_immediately(self, alert: Alert, user: User, 
                                    channel: DeliveryChannel = DeliveryChannel.IN_APP,
                                    is_reminder: bool = False) -> bool:
        """Schedule and immediately send a notification"""
        delivery = self.schedule_notification(alert, user, channel, is_reminder)
        return self._send_notification(delivery)
    
    def process_reminders(self) -> Dict[str, int]:
        """Process and send reminder notifications"""
        from .alert_service import AlertService
        
        alert_service = AlertService(self.db)
        reminder_data = alert_service.get_alerts_requiring_reminders()
        
        results = {
            'reminders_sent': 0,
            'users_reminded': 0,
            'alerts_processed': len(reminder_data)
        }
        
        for data in reminder_data:
            alert = data['alert']
            users_needing_reminders = data['users']
            
            for user_preference in users_needing_reminders:
                user = self.db.query(User).filter(User.id == user_preference.user_id).first()
                if user:
                    # Calculate reminder sequence
                    reminder_count = user_preference.reminder_count + 1
                    
                    # Send reminder
                    success = self.send_notification_immediately(
                        alert, user, alert.delivery_type, is_reminder=True
                    )
                    
                    if success:
                        # Update user preference
                        user_preference.last_reminded_at = datetime.utcnow()
                        user_preference.reminder_count = reminder_count
                        
                        results['reminders_sent'] += 1
                        results['users_reminded'] += 1
        
        self.db.commit()
        return results
    
    def get_user_notifications(self, user_id: int, 
                             include_read: bool = True,
                             skip: int = 0, limit: int = 50) -> List[Dict]:
        """Get notifications for a specific user with alert details"""
        query = (self.db.query(NotificationDelivery)
                .join(Alert, NotificationDelivery.alert_id == Alert.id)
                .outerjoin(UserAlertPreference, and_(
                    UserAlertPreference.alert_id == Alert.id,
                    UserAlertPreference.user_id == user_id
                ))
                .filter(NotificationDelivery.user_id == user_id)
                .add_columns(
                    Alert.title,
                    Alert.message,
                    Alert.severity,
                    UserAlertPreference.is_read,
                    UserAlertPreference.is_snoozed,
                    UserAlertPreference.snoozed_until
                ))
        
        if not include_read:
            query = query.filter(or_(
                UserAlertPreference.is_read == False,
                UserAlertPreference.is_read.is_(None)
            ))
        
        results = query.order_by(NotificationDelivery.created_at.desc()).offset(skip).limit(limit).all()
        
        notifications = []
        for row in results:
            delivery = row[0]
            alert_title = row[1]
            alert_message = row[2]
            alert_severity = row[3]
            is_read = row[4] if row[4] is not None else False
            is_snoozed = row[5] if row[5] is not None else False
            snoozed_until = row[6]
            
            notifications.append({
                'id': delivery.id,
                'alert_id': delivery.alert_id,
                'alert_title': alert_title,
                'alert_message': alert_message,
                'alert_severity': alert_severity.value if alert_severity else 'info',
                'channel': delivery.channel.value,
                'status': delivery.status.value,
                'scheduled_at': delivery.scheduled_at,
                'sent_at': delivery.sent_at,
                'delivered_at': delivery.delivered_at,
                'read_at': delivery.read_at,
                'is_reminder': delivery.is_reminder,
                'reminder_sequence': delivery.reminder_sequence,
                'is_read': is_read,
                'is_snoozed': is_snoozed,
                'snoozed_until': snoozed_until,
                'created_at': delivery.created_at
            })
        
        return notifications
    
    def mark_notification_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a specific notification as read"""
        delivery = (self.db.query(NotificationDelivery)
                   .filter(and_(
                       NotificationDelivery.id == notification_id,
                       NotificationDelivery.user_id == user_id
                   ))
                   .first())
        
        if delivery:
            delivery.read_at = datetime.utcnow()
            if delivery.status == DeliveryStatus.DELIVERED:
                delivery.status = DeliveryStatus.READ
            self.db.commit()
            return True
        return False
    
    def retry_failed_notifications(self, max_retries: int = 3) -> Dict[str, int]:
        """Retry failed notifications that haven't exceeded max retries"""
        failed_notifications = (self.db.query(NotificationDelivery)
                              .filter(and_(
                                  NotificationDelivery.status == DeliveryStatus.FAILED,
                                  NotificationDelivery.retry_count < max_retries,
                                  or_(
                                      NotificationDelivery.next_retry_at.is_(None),
                                      NotificationDelivery.next_retry_at <= datetime.utcnow()
                                  )
                              ))
                              .all())
        
        results = {
            'retried': 0,
            'succeeded': 0,
            'still_failed': 0
        }
        
        for delivery in failed_notifications:
            delivery.retry_count += 1
            delivery.next_retry_at = datetime.utcnow() + timedelta(minutes=5 * delivery.retry_count)
            
            if self._send_notification(delivery):
                results['succeeded'] += 1
            else:
                results['still_failed'] += 1
            
            results['retried'] += 1
        
        self.db.commit()
        return results
    
    def get_delivery_stats(self) -> Dict[str, int]:
        """Get notification delivery statistics"""
        total_sent = self.db.query(NotificationDelivery).filter(
            NotificationDelivery.status.in_([
                DeliveryStatus.SENT, 
                DeliveryStatus.DELIVERED, 
                DeliveryStatus.READ
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
        
        return {
            'total_sent': total_sent,
            'total_delivered': total_delivered,
            'total_read': total_read,
            'total_failed': total_failed,
            'delivery_rate': (total_delivered / total_sent * 100) if total_sent > 0 else 0,
            'read_rate': (total_read / total_delivered * 100) if total_delivered > 0 else 0
        }
    
    def _send_notification(self, delivery: NotificationDelivery) -> bool:
        """Send a single notification using appropriate channel"""
        try:
            # Get alert and user
            alert = self.db.query(Alert).filter(Alert.id == delivery.alert_id).first()
            user = self.db.query(User).filter(User.id == delivery.user_id).first()
            
            if not alert or not user:
                delivery.status = DeliveryStatus.FAILED
                delivery.error_message = "Alert or user not found"
                return False
            
            # Get appropriate channel
            channel = self.channels.get(delivery.channel)
            if not channel:
                delivery.status = DeliveryStatus.FAILED
                delivery.error_message = f"Unsupported channel: {delivery.channel}"
                return False
            
            # Send notification
            success = channel.send_notification(alert, user, delivery)
            
            if not success:
                delivery.status = DeliveryStatus.FAILED
            
            return success
            
        except Exception as e:
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = str(e)
            return False
    
    def _get_delivery_address(self, user: User, channel: DeliveryChannel) -> Optional[str]:
        """Get delivery address for user based on channel"""
        if channel == DeliveryChannel.EMAIL:
            return user.email
        elif channel == DeliveryChannel.SMS:
            # TODO: Add phone number field to User model
            return None
        else:  # IN_APP
            return None