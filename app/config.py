import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Comprehensive Logistics & Fleet Management Platform"
    PROJECT_NO: str = "P-194"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database: Defaults to SQLite for local zero-config runs, or PostgreSQL via env
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fleet.db")
    
    # Redis configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_IN_MEMORY_REDIS_FALLBACK: bool = True
    
    # Telemetry configuration
    TELEMETRY_BUFFER_BATCH_SIZE: int = 100
    TELEMETRY_FLUSH_INTERVAL_SECONDS: float = 2.0
    GEOFENCE_CORRIDOR_TOLERANCE_KM: float = 35.0
    
    # Security & CORS
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
