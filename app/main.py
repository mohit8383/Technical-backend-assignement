from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
import redis
import json
import logging
from contextlib import asynccontextmanager

from .database import get_db, engine
from .models import Base, Book, Review
from .schemas import BookCreate, BookResponse, ReviewCreate, ReviewResponse
from .cache import get_redis_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Book Review Service",
    description="A simple book review API with caching",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/books", response_model=List[BookResponse])
async def get_books(db: Session = Depends(get_db)):
    """
    Get all books with Redis caching.
    
    First attempts to read from cache, falls back to database if cache is unavailable.
    """
    cache_key = "books:all"
    
    try:
        # Try to get from cache first
        redis_client = get_redis_client()
        cached_books = redis_client.get(cache_key)
        
        if cached_books:
            logger.info("Cache hit for books")
            books_data = json.loads(cached_books)
            return [BookResponse(**book) for book in books_data]
            
    except Exception as e:
        logger.warning(f"Cache unavailable, falling back to database: {e}")
    
    # Cache miss or cache unavailable - fetch from database
    logger.info("Cache miss or unavailable, fetching from database")
    books = db.query(Book).all()
    books_response = [BookResponse.from_orm(book) for book in books]
    
    # Try to populate cache
    try:
        redis_client = get_redis_client()
        books_data = [book.dict() for book in books_response]
        redis_client.setex(cache_key, 300, json.dumps(books_data))  # Cache for 5 minutes
        logger.info("Cache populated with books data")
    except Exception as e:
        logger.warning(f"Failed to populate cache: {e}")
    
    return books_response

@app.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate, db: Session = Depends(get_db)):
    """Create a new book."""
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    # Invalidate cache
    try:
        redis_client = get_redis_client()
        redis_client.delete("books:all")
        logger.info("Cache invalidated after book creation")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache: {e}")
    
    return BookResponse.from_orm(db_book)

@app.get("/books/{book_id}/reviews", response_model=List[ReviewResponse])
async def get_book_reviews(book_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a specific book."""
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # This query will use the index on book_id
    reviews = db.query(Review).filter(Review.book_id == book_id).all()
    return [ReviewResponse.from_orm(review) for review in reviews]

@app.post("/books/{book_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(book_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    """Create a new review for a book."""
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db_review = Review(**review.dict(), book_id=book_id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    return ReviewResponse.from_orm(db_review)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 