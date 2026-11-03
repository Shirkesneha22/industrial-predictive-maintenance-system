"""
Database Configuration and Session Management.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

try:
    from backend.config import settings
except ImportError:
    from config import settings

Base = declarative_base()

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception:
    # Graceful fallback when database driver (e.g., psycopg) is not yet installed in host environment
    engine = None
    SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a database session to API route handlers."""
    if SessionLocal is None:
        raise RuntimeError(
            "Database engine is not initialized. Please ensure database driver (e.g., psycopg[binary]) is installed."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
