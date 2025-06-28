from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Book
from ..schemas import BookCreate, Book as BookSchema, BookWithReviews
from ..dependencies import get_cache, CacheService

router = APIRouter(prefix="/books", tags=["books"])

@router.post("/", response_model=BookSchema, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate, db: Session = Depends(get_db), cache: CacheService = Depends(get_cache)):
    """Create a new book"""
    db_book = Book(title=book.title, author=book.author)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    # Invalidate cache when new book is created
    cache.delete("books:all")
    
    return db_book

@router.get("/", response_model=List[BookSchema])
def get_books(db: Session = Depends(get_db), cache: CacheService = Depends(get_cache)):
    """Get all books with caching"""
    # Try to get from cache first
    cached_books = cache.get("books:all")
    if cached_books:
        return cached_books
    
    # If not in cache, get from database
    books = db.query(Book).all()
    book_list = [{"id": book.id, "title": book.title, "author": book.author} for book in books]
    
    # Store in cache
    cache.set("books:all", book_list)
    
    return book_list

@router.get("/{book_id}", response_model=BookWithReviews)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get a specific book with its reviews"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book

@router.put("/{book_id}", response_model=BookSchema)
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db), cache: CacheService = Depends(get_cache)):
    """Update a book"""
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    db_book.title = book.title
    db_book.author = book.author
    db.commit()
    db.refresh(db_book)
    
    # Invalidate cache
    cache.delete("books:all")
    
    return db_book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db), cache: CacheService = Depends(get_cache)):
    """Delete a book"""
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    db.delete(db_book)
    db.commit()
    
    # Invalidate cache
    cache.delete("books:all")
    
    return None 