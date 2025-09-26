from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import create_tables
from app.router import (
    users_router, teams_router, alerts_router, 
    notifications_router, analytics_router
)

app = FastAPI(
    title=settings.app_name,
    description="A lightweight alerting and notification system with clean OOP design",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    create_tables()
    print("Database tables created successfully")

@app.get("/")
async def root():
    return {
        "message": "Alerting & Notification Platform API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "alerting-platform",
        "version": "1.0.0"
    }
