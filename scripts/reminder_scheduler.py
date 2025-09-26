"""
Background task scheduler for processing reminders
In production, this would be replaced by a proper task queue like Celery
"""
import asyncio
import time
from datetime import datetime
from app.core.database import SessionLocal
from app.services.notification_service import NotificationService

async def process_reminders_job():
    """Background job to process reminder notifications"""
    while True:
        try:
            print(f"[{datetime.now()}] Processing reminders...")
            
            db = SessionLocal()
            notification_service = NotificationService(db)
            
            # Process reminders
            results = notification_service.process_reminders()
            
            if results['reminders_sent'] > 0:
                print(f"✅ Sent {results['reminders_sent']} reminders to {results['users_reminded']} users")
            else:
                print("📭 No reminders to send")
            
            db.close()
            
        except Exception as e:
            print(f"❌ Error processing reminders: {e}")
        
        # Wait 30 minutes before next check (configurable)
        await asyncio.sleep(1800)  # 1800 seconds = 30 minutes

if __name__ == "__main__":
    print("🚀 Starting reminder scheduler...")
    print("⏰ Checking for reminders every 30 minutes")
    asyncio.run(process_reminders_job())
