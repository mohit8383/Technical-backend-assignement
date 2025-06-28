# Book Review Service

A RESTful API for managing books and reviews built with FastAPI, SQLAlchemy, and Redis caching.

## Features

- **Books Management**: CRUD operations for books
- **Reviews Management**: CRUD operations for book reviews
- **Caching**: Redis-based caching with graceful fallback
- **Database Migrations**: Alembic for database schema management
- **Comprehensive Testing**: Unit tests and integration tests
- **API Documentation**: Auto-generated with FastAPI

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (configurable to PostgreSQL)
- **ORM**: SQLAlchemy
- **Caching**: Redis
- **Migrations**: Alembic
- **Testing**: pytest
- **Documentation**: OpenAPI/Swagger

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── dependencies.py      # Dependency injection
└── routers/
    ├── __init__.py
    ├── books.py         # Books endpoints
    └── reviews.py       # Reviews endpoints
tests/
├── __init__.py
├── test_books.py        # Books tests
├── test_reviews.py      # Reviews tests
└── test_cache.py        # Cache integration tests
alembic/                 # Database migrations
requirements.txt         # Python dependencies
README.md               # This file
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
# Database configuration
DATABASE_URL=sqlite:///./book_review.db

# Redis configuration
REDIS_URL=redis://localhost:6379
CACHE_TTL=300

# Application configuration
DEBUG=true
```

### 3. Database Setup

Initialize and run database migrations:

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 4. Run the Application

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_books.py
```

## API Endpoints

### Books

- `POST /books/` - Create a new book
- `GET /books/` - Get all books (cached)
- `GET /books/{book_id}` - Get a specific book with reviews
- `PUT /books/{book_id}` - Update a book
- `DELETE /books/{book_id}` - Delete a book

### Reviews

- `POST /reviews/` - Create a new review
- `GET /reviews/` - Get all reviews
- `GET /reviews/{review_id}` - Get a specific review
- `GET /reviews/book/{book_id}` - Get reviews for a specific book
- `PUT /reviews/{review_id}` - Update a review
- `DELETE /reviews/{review_id}` - Delete a review

### Health Check

- `GET /` - API information
- `GET /health` - Health check

## API Documentation

Once the application is running, you can access:

- **Interactive API Documentation**: http://localhost:8000/docs
- **Alternative API Documentation**: http://localhost:8000/redoc

## Database Schema

### Books Table
- `id` (Integer, Primary Key)
- `title` (String, Required)
- `author` (String, Required)

### Reviews Table
- `id` (Integer, Primary Key)
- `text` (Text, Required)
- `rating` (Integer, Optional, 1-5)
- `book_id` (Integer, Foreign Key to books.id)

**Index**: `idx_reviews_book_id` on `reviews.book_id`

## Caching Strategy

The application implements Redis caching with the following features:

- **Cache Hit**: Returns data from Redis
- **Cache Miss**: Fetches from database, stores in Redis, returns data
- **Cache Invalidation**: Automatically invalidates cache on data changes
- **Graceful Fallback**: Continues working even if Redis is unavailable

### Cache Keys
- `books:all` - Cached list of all books

## Testing

The application includes comprehensive tests:

### Unit Tests
- Book CRUD operations
- Review CRUD operations
- Input validation
- Error handling

### Integration Tests
- Cache hit/miss scenarios
- Cache failure graceful fallback
- Cache invalidation on data changes

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_books.py
pytest tests/test_reviews.py
pytest tests/test_cache.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

## Development

### Adding New Endpoints

1. Create or update schemas in `app/schemas.py`
2. Add endpoint logic in appropriate router file
3. Add tests in corresponding test file
4. Update this README if needed

### Database Changes

1. Update models in `app/models.py`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Apply migration: `alembic upgrade head`
4. Update tests if needed

### Cache Strategy

When adding new cached endpoints:

1. Implement cache logic in the endpoint
2. Add cache invalidation on data changes
3. Add cache tests in `tests/test_cache.py`

## Production Deployment

### Environment Variables

For production, update the `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost/book_review
REDIS_URL=redis://redis-server:6379
CACHE_TTL=300
DEBUG=false
```

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN alembic upgrade head

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Error Handling

The application includes comprehensive error handling:

- **404 Not Found**: Resource doesn't exist
- **422 Validation Error**: Invalid input data
- **500 Internal Server Error**: Server-side errors

## Performance Considerations

- Database indexes on frequently queried fields
- Redis caching for read-heavy operations
- Connection pooling for database connections
- Graceful cache fallback for reliability

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. 