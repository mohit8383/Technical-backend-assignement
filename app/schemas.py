from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Book schemas
class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Book(BookBase):
    id: int
    
    class Config:
        from_attributes = True

# Review schemas
class ReviewBase(BaseModel):
    text: str = Field(..., min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)

class ReviewCreate(BaseModel):
    reviewer_name: str = Field(..., min_length=1, max_length=255)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    book_id: int
    reviewer_name: str
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Review(ReviewBase):
    id: int
    book_id: int
    
    class Config:
        from_attributes = True

# Book with reviews
class BookWithReviews(Book):
    reviews: List[Review] = [] 