"""
Seed script to populate the database with sample data for testing
"""
from sqlalchemy.orm import Session
from ..app.core.database import SessionLocal, create_tables
from ..app.models.user import User
from ..app.models.team import Team
from ..app.models.alert import Alert, SeverityLevel, DeliveryType, VisibilityType, AlertStatus
from ..app.models.user_alert_preference import UserAlertPreference
from datetime import datetime, timedelta
import json

def seed_database():
    """Seed the database with sample data"""
    create_tables()
    db = SessionLocal()
    
    try:
        print("🌱 Seeding database with sample data...")
        
        # Create Teams
        teams_data = [
            {"name": "Engineering", "description": "Software development team"},
            {"name": "Marketing", "description": "Marketing and growth team"},
            {"name": "Operations", "description": "Operations and infrastructure team"},
            {"name": "Design", "description": "Product design team"}
        ]
        
        teams = []
        for team_data in teams_data:
            existing = db.query(Team).filter(Team.name == team_data["name"]).first()
            if not existing:
                team = Team(**team_data)
                db.add(team)
                teams.append(team)
            else:
                teams.append(existing)
        
        db.commit()
        print(f"✅ Created {len(teams)} teams")
        
        # Create Users
        users_data = [
            # Admins
            {"name": "Alice Admin", "email": "alice@company.com", "is_admin": True, "team_id": teams[0].id},
            {"name": "Bob Manager", "email": "bob@company.com", "is_admin": True, "team_id": teams[1].id},
            
            # Regular Users
            {"name": "Charlie Developer", "email": "charlie@company.com", "is_admin": False, "team_id": teams[0].id},
            {"name": "Diana Designer", "email": "diana@company.com", "is_admin": False, "team_id": teams[3].id},
            {"name": "Eve Engineer", "email": "eve@company.com", "is_admin": False, "team_id": teams[0].id},
            {"name": "Frank Marketer", "email": "frank@company.com", "is_admin": False, "team_id": teams[1].id},
            {"name": "Grace Ops", "email": "grace@company.com", "is_admin": False, "team_id": teams[2].id},
            {"name": "Henry Developer", "email": "henry@company.com", "is_admin": False, "team_id": teams[0].id}
        ]
        
        users = []
        for user_data in users_data:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                user = User(**user_data)
                db.add(user)
                users.append(user)
            else:
                users.append(existing)
        
        db.commit()
        print(f"✅ Created {len(users)} users")
        
        # Create Sample Alerts
        alerts_data = [
            {
                "title": "System Maintenance Window",
                "message": "Scheduled maintenance will occur this weekend. Please save your work.",
                "severity": SeverityLevel.WARNING,
                "delivery_type": DeliveryType.IN_APP,
                "visibility_type": VisibilityType.ORGANIZATION,
                "created_by": users[0].id,  # Alice Admin
                "start_time": datetime.utcnow(),
                "expiry_time": datetime.utcnow() + timedelta(days=7),
                "reminder_interval_hours": 2
            },
            {
                "title": "Security Update Required",
                "message": "Please update your passwords and enable 2FA by end of week.",
                "severity": SeverityLevel.CRITICAL,
                "delivery_type": DeliveryType.IN_APP,
                "visibility_type": VisibilityType.ORGANIZATION,
                "created_by": users[0].id,
                "start_time": datetime.utcnow(),
                "expiry_time": datetime.utcnow() + timedelta(days=14),
                "reminder_interval_hours": 4
            },
            {
                "title": "Engineering Team Meeting",
                "message": "Sprint planning meeting tomorrow at 10 AM in conference room A.",
                "severity": SeverityLevel.INFO,
                "delivery_type": DeliveryType.IN_APP,
                "visibility_type": VisibilityType.TEAM,
                "target_team_ids": json.dumps([teams[0].id]),  # Engineering team
                "created_by": users[0].id,
                "start_time": datetime.utcnow(),
                "expiry_time": datetime.utcnow() + timedelta(days=1)
            },
            {
                "title": "Marketing Campaign Launch",
                "message": "New product launch campaign goes live next Monday. All hands on deck!",
                "severity": SeverityLevel.WARNING,
                "delivery_type": DeliveryType.IN_APP,
                "visibility_type": VisibilityType.TEAM,
                "target_team_ids": json.dumps([teams[1].id]),  # Marketing team
                "created_by": users[1].id,  # Bob Manager
                "start_time": datetime.utcnow(),
                "expiry_time": datetime.utcnow() + timedelta(days=3)
            },
            {
                "title": "Personal Task Reminder",
                "message": "Don't forget to submit your quarterly review by Friday.",
                "severity": SeverityLevel.INFO,
                "delivery_type": DeliveryType.IN_APP,
                "visibility_type": VisibilityType.USER,
                "target_user_ids": json.dumps([users[2].id]),  # Charlie Developer
                "created_by": users[0].id,
                "start_time": datetime.utcnow(),
                "expiry_time": datetime.utcnow() + timedelta(days=5)
            }
        ]
        
        alerts = []
        for alert_data in alerts_data:
            alert = Alert(**alert_data)
            db.add(alert)
            alerts.append(alert)
        
        db.commit()
        print(f"✅ Created {len(alerts)} alerts")
        
        # Create User Alert Preferences (simulate some interactions)
        preferences_data = []
        
        # Organization-wide alerts - create preferences for all users
        org_alerts = [a for a in alerts if a.visibility_type == VisibilityType.ORGANIZATION]
        for alert in org_alerts:
            for user in users:
                pref = UserAlertPreference(
                    user_id=user.id,
                    alert_id=alert.id,
                    is_read=user.id % 3 == 0,  # Some users have read it
                    is_snoozed=user.id % 5 == 0,  # Some users have snoozed it
                    snooze_count=1 if user.id % 5 == 0 else 0
                )
                if pref.is_read:
                    pref.read_at = datetime.utcnow() - timedelta(hours=2)
                if pref.is_snoozed:
                    pref.snoozed_at = datetime.utcnow() - timedelta(hours=1)
                    pref.snoozed_until = datetime.utcnow() + timedelta(hours=10)
                
                preferences_data.append(pref)
        
        # Team-specific alerts
        team_alerts = [a for a in alerts if a.visibility_type == VisibilityType.TEAM]
        for alert in team_alerts:
            target_team_ids = json.loads(alert.target_team_ids) if alert.target_team_ids else []
            team_users = [u for u in users if u.team_id in target_team_ids]
            
            for user in team_users:
                pref = UserAlertPreference(
                    user_id=user.id,
                    alert_id=alert.id,
                    is_read=user.id % 4 == 0,
                    is_snoozed=False,
                    reminder_count=1 if user.id % 3 == 0 else 0
                )
                if pref.is_read:
                    pref.read_at = datetime.utcnow() - timedelta(hours=1)
                if pref.reminder_count > 0:
                    pref.last_reminded_at = datetime.utcnow() - timedelta(hours=3)
                
                preferences_data.append(pref)
        
        # User-specific alerts
        user_alerts = [a for a in alerts if a.visibility_type == VisibilityType.USER]
        for alert in user_alerts:
            target_user_ids = json.loads(alert.target_user_ids) if alert.target_user_ids else []
            
            for user_id in target_user_ids:
                pref = UserAlertPreference(
                    user_id=user_id,
                    alert_id=alert.id,
                    is_read=False,  # User-specific alerts usually unread
                    is_snoozed=False,
                    reminder_count=2
                )
                pref.last_reminded_at = datetime.utcnow() - timedelta(hours=4)
                preferences_data.append(pref)
        
        for pref in preferences_data:
            db.add(pref)
        
        db.commit()
        print(f"✅ Created {len(preferences_data)} user alert preferences")
        
        print("\n🎉 Database seeded successfully!")
        print("\n📊 Sample Data Summary:")
        print(f"   Teams: {len(teams)}")
        print(f"   Users: {len(users)} (2 admins, {len(users)-2} regular users)")
        print(f"   Alerts: {len(alerts)}")
        print(f"   User Preferences: {len(preferences_data)}")
        
        print("\n🔑 Sample Admin Users:")
        print("   Alice Admin (alice@company.com) - User ID: 1")
        print("   Bob Manager (bob@company.com) - User ID: 2")
        
        print("\n📝 API Usage Examples:")
        print("   # Login as admin:")
        print("   curl -X POST http://localhost:8000/api/v1/users/login \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"email\": \"alice@company.com\"}'")
        print()
        print("   # Get alerts for user (add X-User-ID header):")
        print("   curl -X GET http://localhost:8000/api/v1/alerts/me \\")
        print("        -H 'X-User-ID: 1'")
        print()
        print("   # View analytics dashboard:")
        print("   curl -X GET http://localhost:8000/api/v1/analytics/dashboard \\")
        print("        -H 'X-User-ID: 1'")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()