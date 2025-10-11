from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://labmate:labmate_password@postgres:5432/labmate_db"
    
    # Security
    BETA_KEY: str = "your_beta_key_here"
    
    # File paths
    UPLOAD_DIR: str = "/app/uploads"
    SCREENSHOT_DIR: str = "/app/screenshots"
    REPORT_DIR: str = "/app/reports"
    
    # Docker settings
    DOCKER_IMAGE: str = "python:3.10-slim"
    CONTAINER_TIMEOUT: int = 30
    MEMORY_LIMIT: str = "512m"
    CPU_PERIOD: int = 100000
    CPU_QUOTA: int = 50000
    
    # File limits
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    MAX_CODE_LENGTH: int = 5000
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 4000
    
    class Config:
        env_file = ".env"


settings = Settings()
