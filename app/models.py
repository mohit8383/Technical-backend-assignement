from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    
    # Relationship with reviews
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # Optional rating
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    
    # Relationship with book
    book = relationship("Book", back_populates="reviews")

# Create index on book_id for better query performance
Index('idx_reviews_book_id', Review.book_id) 