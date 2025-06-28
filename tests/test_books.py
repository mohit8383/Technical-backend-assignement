
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import Book
from app.dependencies import CacheService
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
    """Mock cache service for testing"""
    def __init__(self):
        self.cache = {}
    
    def get(self, key: str):
        return self.cache.get(key)
    
    def set(self, key: str, value, ttl=None):
        self.cache[key] = value
        return True
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
        return True

def override_get_cache():
    """Override cache dependency for testing"""
    return MockCacheService()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def test_db():
    """Create a clean test database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_cache():
    """Create a mock cache for testing"""
    return MockCacheService()

class TestBooks:
    def test_create_book(self, test_db):
        """Test creating a new book"""
        book_data = {"title": "Test Book", "author": "Test Author"}
        response = client.post("/books/", json=book_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == book_data["title"]
        assert data["author"] == book_data["author"]
        assert "id" in data
    
    def test_get_books_empty(self, test_db):
        """Test getting books when database is empty"""
        response = client.get("/books/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_books_with_data(self, test_db):
        """Test getting books with data"""
        # Create a book first
        book_data = {"title": "Test Book", "author": "Test Author"}
        client.post("/books/", json=book_data)
        
        # Get all books
        response = client.get("/books/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == book_data["title"]
        assert data[0]["author"] == book_data["author"]
    
    def test_get_book_by_id(self, test_db):
        """Test getting a specific book by ID"""
        # Create a book first
        book_data = {"title": "Test Book", "author": "Test Author"}
        create_response = client.post("/books/", json=book_data)
        book_id = create_response.json()["id"]
        
        # Get the book by ID
        response = client.get(f"/books/{book_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == book_data["title"]
        assert data["author"] == book_data["author"]
        assert data["reviews"] == []
    
    def test_get_book_not_found(self, test_db):
        """Test getting a book that doesn't exist"""
        response = client.get("/books/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"
    
    def test_update_book(self, test_db):
        """Test updating a book"""
        # Create a book first
        book_data = {"title": "Test Book", "author": "Test Author"}
        create_response = client.post("/books/", json=book_data)
        book_id = create_response.json()["id"]
        
        # Update the book
        update_data = {"title": "Updated Book", "author": "Updated Author"}
        response = client.put(f"/books/{book_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["author"] == update_data["author"]
    
    def test_delete_book(self, test_db):
        """Test deleting a book"""
        # Create a book first
        book_data = {"title": "Test Book", "author": "Test Author"}
        create_response = client.post("/books/", json=book_data)
        book_id = create_response.json()["id"]
        
        # Delete the book
        response = client.delete(f"/books/{book_id}")
        
        assert response.status_code == 204
        
        # Verify book is deleted
        get_response = client.get(f"/books/{book_id}")
        assert get_response.status_code == 404 