from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import os

# Check if DATABASE_URL is set
if not settings.DATABASE_URL:
    print("⚠ WARNING: DATABASE_URL is empty. Database features will be disabled.")
    # Create a dummy engine for development
    engine = None
    SessionLocal = None
    Base = declarative_base()
else:
    # Create database engine with Railway-optimized settings
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        echo=False           # Set to True for debugging
    )
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create base class for models
    Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    if SessionLocal is None:
        raise Exception("Database not configured. Please set DATABASE_URL environment variable.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
