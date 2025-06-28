from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Review, Book
from ..schemas import ReviewCreate, Review as ReviewSchema
from ..dependencies import get_cache, CacheService

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
def create_review(review: ReviewCreate, db: Session = Depends(get_db), cache: CacheService = Depends(get_cache)):
    """Create a new review"""
    # Check if book exists
    book = db.query(Book).filter(Book.id == review.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    db_review = Review(
        text=review.text,
        rating=review.rating,
        book_id=review.book_id
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Invalidate cache for books
    cache.delete("books:all")
    
    return db_review

@router.get("/", response_model=List[ReviewSchema])
def get_reviews(db: Session = Depends(get_db)):
    """Get all reviews"""
    reviews = db.query(Review).all()
    return reviews

@router.get("/{review_id}", response_model=ReviewSchema)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get a specific review"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    return review

@router.get("/book/{book_id}", response_model=List[ReviewSchema])
def get_reviews_by_book(book_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a specific book"""
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    reviews = db.query(Review).filter(Review.book_id == book_id).all()
    return reviews

@router.put("/{review_id}", response_model=ReviewSchema)
def update_review(review_id: int, review: ReviewCreate, db: Session = Depends(get_db), cache: CacheService = Depends(get_cache)):
    """Update a review"""
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if book exists
    book = db.query(Book).filter(Book.id == review.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    db_review.text = review.text
    db_review.rating = review.rating
    db_review.book_id = review.book_id
    db.commit()
    db.refresh(db_review)
    
    # Invalidate cache
    cache.delete("books:all")
    
    return db_review

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: Session = Depends(get_db), cache: CacheService = Depends(get_cache)):
    """Delete a review"""
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    db.delete(db_review)
    db.commit()
    
    # Invalidate cache
    cache.delete("books:all")
    
    return None 