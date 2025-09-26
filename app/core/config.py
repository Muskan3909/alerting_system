from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./alerting.db"
    secret_key: str = "your-secret-key-here"
    app_name: str = "Alerting & Notification Platform"
    debug: bool = True
    reminder_interval_hours: int = 2
    
    class Config:
        env_file = ".env"

settings = Settings()