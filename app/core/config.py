from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "QOVES Face Segmentation API"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "qoves_db"
    DATABASE_URL: Optional[str] = None
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Performance
    LOAD_TEST_MODE: bool = False
    SIMULATION_DELAY: int = 20
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()