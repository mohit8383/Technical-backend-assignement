import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import Book, Review
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

@pytest.fixture
def test_db():
    """Create a clean test database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_book(test_db):
    """Create a sample book for testing"""
    book_data = {"title": "Test Book", "author": "Test Author"}
    response = client.post("/books/", json=book_data)
    return response.json()

class TestReviews:
    def test_create_review(self, test_db, sample_book):
        """Test creating a new review"""
        review_data = {
            "text": "Great book!",
            "rating": 5,
            "book_id": sample_book["id"]
        }
        response = client.post("/reviews/", json=review_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["text"] == review_data["text"]
        assert data["rating"] == review_data["rating"]
        assert data["book_id"] == sample_book["id"]
        assert "id" in data
    
    def test_create_review_without_rating(self, test_db, sample_book):
        """Test creating a review without rating"""
        review_data = {
            "text": "Good book!",
            "book_id": sample_book["id"]
        }
        response = client.post("/reviews/", json=review_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["text"] == review_data["text"]
        assert data["rating"] is None
        assert data["book_id"] == sample_book["id"]
    
    def test_create_review_book_not_found(self, test_db):
        """Test creating a review for non-existent book"""
        review_data = {
            "text": "Great book!",
            "rating": 5,
            "book_id": 999
        }
        response = client.post("/reviews/", json=review_data)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"
    
    def test_get_reviews_empty(self, test_db):
        """Test getting reviews when database is empty"""
        response = client.get("/reviews/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_reviews_with_data(self, test_db, sample_book):
        """Test getting all reviews"""
        # Create a review first
        review_data = {
            "text": "Great book!",
            "rating": 5,
            "book_id": sample_book["id"]
        }
        client.post("/reviews/", json=review_data)
        
        # Get all reviews
        response = client.get("/reviews/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["text"] == review_data["text"]
        assert data[0]["rating"] == review_data["rating"]
    
    def test_get_review_by_id(self, test_db, sample_book):
        """Test getting a specific review by ID"""
        # Create a review first
        review_data = {
            "text": "Great book!",
            "rating": 5,
            "book_id": sample_book["id"]
        }
        create_response = client.post("/reviews/", json=review_data)
        review_id = create_response.json()["id"]
        
        # Get the review by ID
        response = client.get(f"/reviews/{review_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == review_data["text"]
        assert data["rating"] == review_data["rating"]
        assert data["book_id"] == sample_book["id"]
    
    def test_get_review_not_found(self, test_db):
        """Test getting a review that doesn't exist"""
        response = client.get("/reviews/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Review not found"
    
    def test_get_reviews_by_book(self, test_db, sample_book):
        """Test getting reviews for a specific book"""
        # Create reviews for the book
        review_data1 = {
            "text": "Great book!",
            "rating": 5,
            "book_id": sample_book["id"]
        }
        review_data2 = {
            "text": "Amazing read!",
            "rating": 4,
            "book_id": sample_book["id"]
        }
        client.post("/reviews/", json=review_data1)
        client.post("/reviews/", json=review_data2)
        
        # Get reviews for the book
        response = client.get(f"/reviews/book/{sample_book['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(review["book_id"] == sample_book["id"] for review in data)
    
    def test_get_reviews_by_book_not_found(self, test_db):
        """Test getting reviews for non-existent book"""
        response = client.get("/reviews/book/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"
    
    def test_update_review(self, test_db, sample_book):
        """Test updating a review"""
        # Create a review first
        review_data = {
            "text": "Great book!",
            "rating": 5,
            "book_id": sample_book["id"]
        }
        create_response = client.post("/reviews/", json=review_data)
        review_id = create_response.json()["id"]
        
        # Update the review
        update_data = {
            "text": "Updated review!",
            "rating": 4,
            "book_id": sample_book["id"]
        }
        response = client.put(f"/reviews/{review_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == update_data["text"]
        assert data["rating"] == update_data["rating"]
    
    def test_delete_review(self, test_db, sample_book):
        """Test deleting a review"""
        # Create a review first
        review_data = {
            "text": "Great book!",
            "rating": 5,
            "book_id": sample_book["id"]
        }
        create_response = client.post("/reviews/", json=review_data)
        review_id = create_response.json()["id"]
        
        # Delete the review
        response = client.delete(f"/reviews/{review_id}")
        
        assert response.status_code == 204
        
        # Verify review is deleted
        get_response = client.get(f"/reviews/{review_id}")
        assert get_response.status_code == 404

def test_create_review(client):
    """Unit test: Create a review for a book"""
    # First create a book
    book_data = {"title": "Review Test Book", "author": "Test Author"}
    book_response = client.post("/books", json=book_data)
    book_id = book_response.json()["id"]
    
    # Create a review
    review_data = {
        "reviewer_name": "Test Reviewer",
        "rating": 5,
        "comment": "Great book!"
    }
    
    response = client.post(f"/books/{book_id}/reviews", json=review_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["reviewer_name"] == review_data["reviewer_name"]
    assert data["rating"] == review_data["rating"]
    assert data["comment"] == review_data["comment"]
    assert data["book_id"] == book_id

def test_get_book_reviews(client):
    """Test getting reviews for a book"""
    # Create a book
    book_data = {"title": "Book with Reviews", "author": "Test Author"}
    book_response = client.post("/books", json=book_data)
    book_id = book_response.json()["id"]
    
    # Create multiple reviews
    reviews = [
        {"reviewer_name": "Reviewer 1", "rating": 5, "comment": "Excellent!"},
        {"reviewer_name": "Reviewer 2", "rating": 4, "comment": "Good read"},
    ]
    
    for review in reviews:
        client.post(f"/books/{book_id}/reviews", json=review)
    
    # Get reviews
    response = client.get(f"/books/{book_id}/reviews")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_create_review_nonexistent_book(client):
    """Test creating a review for a non-existent book"""
    review_data = {
        "reviewer_name": "Test Reviewer",
        "rating": 5,
        "comment": "Great book!"
    }
    
    response = client.post("/books/999/reviews", json=review_data)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

def test_get_reviews_nonexistent_book(client):
    """Test getting reviews for a non-existent book"""
    response = client.get("/books/999/reviews")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found" 