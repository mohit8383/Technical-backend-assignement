from pydantic import BaseModel, Field
from typing import List, Optional

# Book schemas
class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    
    class Config:
        from_attributes = True

# Review schemas
class ReviewBase(BaseModel):
    text: str = Field(..., min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)

class ReviewCreate(ReviewBase):
    book_id: int

class Review(ReviewBase):
    id: int
    book_id: int
    
    class Config:
        from_attributes = True

# Book with reviews
class BookWithReviews(Book):
    reviews: List[Review] = [] 