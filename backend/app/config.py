import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Concave Support Ticketing System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./concave_tickets.db")
    
    # JWT Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "concave-super-secret-jwt-key-for-assessment-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # SLA Defaults (hours)
    DEFAULT_TAT_HIGH: int = 4
    DEFAULT_TAT_MEDIUM: int = 24
    DEFAULT_TAT_LOW: int = 48
    
    # Policy Defaults
    DEFAULT_REOPEN_WINDOW_DAYS: int = 7
    DEFAULT_MAX_REOPEN_ATTEMPTS: int = 2
    DEFAULT_AUTO_CLOSE_DAYS: int = 7

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
