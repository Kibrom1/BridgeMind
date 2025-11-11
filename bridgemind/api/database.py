"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
from typing import Generator

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bridgemind:bridgemind_dev@localhost:5433/bridgemind"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # For development
    echo=False  # Set to True for SQL logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    Use with FastAPI Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

