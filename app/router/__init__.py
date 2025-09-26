# app/routers/__init__.py
from .users import router as users_router
from .teams import router as teams_router
from .alerts import router as alerts_router
from .notifications import router as notifications_router
from .analytics import router as analytics_router

__all__ = [
    "users_router",
    "teams_router", 
    "alerts_router",
    "notifications_router",
    "analytics_router"
]