# Alerting & Notification Platform

A lightweight, extensible alerting and notification system built with **FastAPI** and **SQLAlchemy**.  
Designed with clean OOP principles and robust admin/user functionality, it ensures timely alerts and reminders for critical events.

📂 Repository:(https://github.com/Muskan3909/alerting_system)

## 🚀 Features

### Core Functionality
- **Alert Management**: Create, update, archive alerts with flexible targeting
- **Multi-level Visibility**: Organization, team, and user-specific alerts
- **Smart Reminders**: Configurable reminder frequency (default: every 2 hours)
- **User Controls**: Read/unread status, snooze functionality (until end of day)
- **Analytics Dashboard**: Comprehensive metrics and performance tracking

### Technical Excellence
- **Clean OOP Design**: Strategy, Observer, and Repository patterns
- **Extensible Architecture**: Easy to add new notification channels
- **Type Safety**: Full Pydantic schema validation
- **Database Relations**: Proper SQLAlchemy relationships and constraints
- **REST API**: Comprehensive endpoints with OpenAPI documentation

## 🏗️ Architecture

### Design Patterns Used
1. **Strategy Pattern**: Notification channels (In-App, Email, SMS)
2. **Repository Pattern**: Service layer abstraction
3. **Observer Pattern**: User subscription to alerts
4. **State Pattern**: Alert lifecycle management

### Project Structure
```
alerting_system/
├── app/
│   ├── core/           # Configuration and database
│   ├── models/         # SQLAlchemy database models
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business logic layer
│   ├── routers/        # FastAPI route handlers
│   └── scripts/        # Database seeding and background tasks
├── .env                # Environment configuration
├── main.py             # Application entry point
└── requirements.txt    # Python dependencies
```

## 📦 Installation

### Prerequisites
- Python 3.13.7
- SQLite (included with Python)

### Setup Steps

1. **Clone and navigate to the project**:
```bash
git clone <repository-url>
cd alerting_system
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create environment file**:
```bash
# Create .env file
echo "DATABASE_URL=sqlite:///./alerting.db" > .env
echo "SECRET_KEY=dev-secret-key" >> .env
echo "DEBUG=True" >> .env
```

4. **Seed the database with sample data**:
```bash
python -m app.scripts.seed_data
```

5. **Start the application**:
```bash
python main.py
```

## 🌐 API Usage

### Authentication (MVP)
The system uses simple header-based authentication. Include the user ID in the `X-User-ID` header:
```bash
curl -H "X-User-ID: 1" http://localhost:8000/api/v1/alerts/me
```

### Key Endpoints

#### User Authentication
```bash
# Login (returns user info)
POST /api/v1/users/login
{
  "email": "alice@company.com"
}
```

#### Alert Management (Admin)
```bash
# Create alert
POST /api/v1/alerts/
{
  "title": "System Maintenance",
  "message": "Scheduled maintenance tonight",
  "severity": "warning",
  "visibility_type": "organization"
}

# List alerts with filtering
GET /api/v1/alerts/?severity=critical&status=active
```

#### User Alert Interaction
```bash
# Get my alerts
GET /api/v1/alerts/me

# Mark alert as read
POST /api/v1/alerts/mark-read
{
  "alert_id": 1
}

# Snooze alert until end of day
POST /api/v1/alerts/snooze
{
  "alert_id": 1
}
```

#### Analytics Dashboard
```bash
# Comprehensive analytics
GET /api/v1/analytics/dashboard

# Alert performance metrics
GET /api/v1/analytics/alert/1

# User engagement metrics
GET /api/v1/analytics/user/1
```

## 🎯 Sample Data

The seed script creates:
- **4 Teams**: Engineering, Marketing, Operations, Design
- **8 Users**: 2 admins, 6 regular users
- **5 Sample Alerts**: Various types and severities
- **User Preferences**: Simulated read/snooze interactions

### Sample Admin Users
- Alice Admin: `alice@company.com` (User ID: 1)
- Bob Manager: `bob@company.com` (User ID: 2)

## 🔧 Configuration

### Environment Variables
```env
DATABASE_URL=sqlite:///./alerting.db
SECRET_KEY=your-secret-key
DEBUG=True
REMINDER_INTERVAL_HOURS=2
```

### Reminder Processing
For production, run the background reminder processor:
```bash
python -m app.scripts.reminder_scheduler
```

## 📊 API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🧪 Testing the System

### 1. Basic Workflow Test
```bash
# 1. Login as admin
curl -X POST http://localhost:8000/api/v1/users/login \
     -H 'Content-Type: application/json' \
     -d '{"email": "alice@company.com"}'

# 2. Create an alert
curl -X POST http://localhost:8000/api/v1/alerts/ \
     -H 'Content-Type: application/json' \
     -H 'X-User-ID: 1' \
     -d '{
       "title": "Test Alert",
       "message": "This is a test alert",
       "severity": "info",
       "visibility_type": "organization"
     }'

# 3. Check alerts as a user
curl -X GET http://localhost:8000/api/v1/alerts/me \
     -H 'X-User-ID: 3'

# 4. Mark alert as read
curl -X POST http://localhost:8000/api/v1/alerts/mark-read \
     -H 'Content-Type: application/json' \
     -H 'X-User-ID: 3' \
     -d '{"alert_id": 6}'
```

### 2. Analytics Test
```bash
# View comprehensive analytics
curl -X GET http://localhost:8000/api/v1/analytics/dashboard \
     -H 'X-User-ID: 1'
```

## 🚀 Production Considerations

### Scalability Improvements
1. **Task Queue**: Replace reminder scheduler with Celery/Redis
2. **Database**: Migrate to PostgreSQL for production
3. **Authentication**: Implement JWT tokens with proper user management
4. **Caching**: Add Redis for frequently accessed data
5. **Monitoring**: Add logging, metrics, and health checks

### Security Enhancements
1. **Rate Limiting**: Prevent API abuse
2. **Input Validation**: Enhanced sanitization
3. **HTTPS**: TLS encryption for all communications
4. **CORS**: Proper origin configuration

## 🎯 Key Design Decisions

1. **Service Layer**: Business logic separated from HTTP handlers
2. **Pydantic Schemas**: Type safety and automatic validation
3. **Database Relationships**: Proper foreign keys and cascading
4. **Flexible Targeting**: JSON arrays for team/user targeting
5. **State Management**: Clean alert lifecycle with status tracking

## 📈 Future Enhancements

- **Email/SMS Channels**: Implement actual delivery mechanisms
- **Escalation Rules**: Auto-escalate unread critical alerts
- **Templates**: Reusable alert templates
- **Webhooks**: External system integrations
- **Mobile Push**: Push notification support

## 🤝 Contributing

This codebase demonstrates clean architecture principles and is ready for extension. Key areas for contribution:
- Additional notification channels
- Advanced analytics features
- Performance optimizations
- Security enhancements
