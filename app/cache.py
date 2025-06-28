import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

def get_redis_client():
    """Get Redis client with connection error handling."""
    return redis.from_url(REDIS_URL, decode_responses=True) 