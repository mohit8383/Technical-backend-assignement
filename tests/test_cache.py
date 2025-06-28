import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import Book
from app.dependencies import get_cache, CacheService
import json

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override dependencies
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

class MockCacheService:
    """Mock cache service for testing cache behavior"""
    def __init__(self, simulate_failure=False):
        self.cache = {}
        self.simulate_failure = simulate_failure
        self.get_calls = 0
        self.set_calls = 0
        self.delete_calls = 0
    
    def get(self, key: str):
        self.get_calls += 1
        if self.simulate_failure:
            return None
        return self.cache.get(key)
    
    def set(self, key: str, value, ttl=None):
        self.set_calls += 1
        if self.simulate_failure:
            return False
        self.cache[key] = value
        return True
    
    def delete(self, key: str):
        self.delete_calls += 1
        if self.simulate_failure:
            return False
        if key in self.cache:
            del self.cache[key]
        return True

def create_mock_cache(simulate_failure=False):
    """Create a mock cache with optional failure simulation"""
    return MockCacheService(simulate_failure)

@pytest.fixture
def test_db():
    """Create a clean test database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestCacheIntegration:
    def test_cache_hit_scenario(self, test_db):
        """Test cache hit - data should be returned from cache"""
        # Override cache dependency with working mock
        mock_cache = create_mock_cache(simulate_failure=False)
        app.dependency_overrides[get_cache] = lambda: mock_cache
        
        # Create a book first
        book_data = {"title": "Test Book", "author": "Test Author"}
        client.post("/books/", json=book_data)
        
        # First request - should hit database and cache the result
        response1 = client.get("/books/")
        assert response1.status_code == 200
        assert len(response1.json()) == 1
        
        # Second request - should hit cache
        response2 = client.get("/books/")
        assert response2.status_code == 200
        assert len(response2.json()) == 1
        
        # Verify cache was used
        assert mock_cache.get_calls >= 2
        assert mock_cache.set_calls >= 1
    
    def test_cache_miss_scenario(self, test_db):
        """Test cache miss - data should be fetched from database"""
        # Override cache dependency with working mock
        mock_cache = create_mock_cache(simulate_failure=False)
        app.dependency_overrides[get_cache] = lambda: mock_cache
        
        # Create a book
        book_data = {"title": "Test Book", "author": "Test Author"}
        client.post("/books/", json=book_data)
        
        # Clear cache to simulate cache miss
        mock_cache.cache.clear()
        
        # Request should fetch from database
        response = client.get("/books/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == book_data["title"]
        assert data[0]["author"] == book_data["author"]
        
        # Verify cache was updated
        cached_data = mock_cache.get("books:all")
        assert cached_data is not None
        assert len(cached_data) == 1
        assert cached_data[0]["title"] == book_data["title"]
    
    def test_cache_failure_graceful_fallback(self, test_db):
        """Test graceful fallback when cache fails"""
        # Override cache dependency with failing mock
        mock_cache = create_mock_cache(simulate_failure=True)
        app.dependency_overrides[get_cache] = lambda: mock_cache
        
        # Create a book
        book_data = {"title": "Test Book", "author": "Test Author"}
        client.post("/books/", json=book_data)
        
        # Request should still work despite cache failure
        response = client.get("/books/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == book_data["title"]
        assert data[0]["author"] == book_data["author"]
        
        # Verify cache was attempted but failed gracefully
        assert mock_cache.get_calls >= 1
        assert mock_cache.set_calls >= 1
    
    def test_cache_invalidation_on_create(self, test_db):
        """Test that cache is invalidated when new book is created"""
        # Override cache dependency with working mock
        mock_cache = create_mock_cache(simulate_failure=False)
        app.dependency_overrides[get_cache] = lambda: mock_cache
        
        # Create initial book and cache it
        book_data1 = {"title": "First Book", "author": "First Author"}
        client.post("/books/", json=book_data1)
        client.get("/books/")  # This will cache the result
        
        # Verify cache has data
        cached_data = mock_cache.get("books:all")
        assert cached_data is not None
        assert len(cached_data) == 1
        
        # Create second book - should invalidate cache
        book_data2 = {"title": "Second Book", "author": "Second Author"}
        client.post("/books/", json=book_data2)
        
        # Verify cache was invalidated
        assert mock_cache.delete_calls >= 1
        
        # Next request should fetch fresh data from database
        response = client.get("/books/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_cache_invalidation_on_update(self, test_db):
        """Test that cache is invalidated when book is updated"""
        # Override cache dependency with working mock
        mock_cache = create_mock_cache(simulate_failure=False)
        app.dependency_overrides[get_cache] = lambda: mock_cache
        
        # Create book and cache it
        book_data = {"title": "Test Book", "author": "Test Author"}
        create_response = client.post("/books/", json=book_data)
        book_id = create_response.json()["id"]
        client.get("/books/")  # This will cache the result
        
        # Update the book - should invalidate cache
        update_data = {"title": "Updated Book", "author": "Updated Author"}
        client.put(f"/books/{book_id}", json=update_data)
        
        # Verify cache was invalidated
        assert mock_cache.delete_calls >= 1
        
        # Next request should fetch updated data
        response = client.get("/books/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == update_data["title"]
        assert data[0]["author"] == update_data["author"]
    
    def test_cache_invalidation_on_delete(self, test_db):
        """Test that cache is invalidated when book is deleted"""
        # Override cache dependency with working mock
        mock_cache = create_mock_cache(simulate_failure=False)
        app.dependency_overrides[get_cache] = lambda: mock_cache
        
        # Create book and cache it
        book_data = {"title": "Test Book", "author": "Test Author"}
        create_response = client.post("/books/", json=book_data)
        book_id = create_response.json()["id"]
        client.get("/books/")  # This will cache the result
        
        # Delete the book - should invalidate cache
        client.delete(f"/books/{book_id}")
        
        # Verify cache was invalidated
        assert mock_cache.delete_calls >= 1
        
        # Next request should show empty list
        response = client.get("/books/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0 