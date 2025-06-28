import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis
from unittest.mock import Mock, patch

from app.main import app
from app.database import get_db, Base
from app.cache import get_redis_client

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

@pytest.fixture
def mock_redis():
    with patch('app.main.get_redis_client') as mock_get_redis:
        mock_redis_client = Mock()
        mock_get_redis.return_value = mock_redis_client
        yield mock_redis_client 