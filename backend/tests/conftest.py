"""
Pytest Fixtures and Test Setup Configuration.
Configures test suite to run against dedicated test database (industrial_maintenance_test).
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings
import backend.database

# Dedicated test database URL
TEST_DB_NAME = os.getenv("TEST_POSTGRES_DB", "industrial_maintenance_test")
TEST_DATABASE_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + f"/{TEST_DB_NAME}"

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Rebind backend.database engine and SessionLocal so all tests, dependencies, and models connect to test DB
backend.database.engine = test_engine
backend.database.SessionLocal = TestSessionLocal

from fastapi.testclient import TestClient

try:
    from backend.main import app
except ImportError:
    from main import app


@pytest.fixture(scope="session")
def client():
    """Provides a TestClient instance for testing API endpoints against test DB."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session against test DB."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
