from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database - Railway will provide DATABASE_URL environment variable
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Validate DATABASE_URL
    if not DATABASE_URL:
        print("⚠ WARNING: DATABASE_URL is not set! Database features will not work.")
        print("Please set DATABASE_URL in Railway environment variables.")
    
    # Security
    BETA_KEY: str = "your_beta_key_here"
    
    # File paths
    UPLOAD_DIR: str = "/app/uploads"
    SCREENSHOT_DIR: str = "/app/screenshots"
    REPORT_DIR: str = "/app/reports"
    REACT_TEMP_DIR: str = "/app/react_temp"
    HOST_PROJECT_ROOT: str = os.getenv("HOST_PROJECT_ROOT", os.getcwd())
    
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
    
    # Web execution settings
    WEB_EXECUTION_TIMEOUT_HTML: int = 10
    WEB_EXECUTION_TIMEOUT_REACT: int = 60
    WEB_EXECUTION_TIMEOUT_NODE: int = 30
    WHITELISTED_NPM_PACKAGES: list = ["express", "react", "react-dom", "vite"]
    
    # React project settings
    REACT_EXECUTION_TIMEOUT: int = 120  # 2 minutes for npm install + startup
    REACT_MULTI_ROUTE_CAPTURE: bool = True
    REACT_DEFAULT_ROUTES: list = ["/", "/about", "/contact"]
    
    class Config:
        env_file = ".env"


settings = Settings()
