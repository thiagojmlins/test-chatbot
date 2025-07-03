import json
import logging
from typing import Any, Optional, Callable, Union
from functools import wraps
import redis
from core.config import REDIS_URL, REDIS_TTL, CACHE_ENABLED

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis cache manager for performance optimization."""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = CACHE_ENABLED
        
        if self.enabled:
            try:
                self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache connection established")
            except Exception as e:
                logger.warning(f"Redis cache not available: {e}")
                self.enabled = False
                self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            ttl = ttl or REDIS_TTL
            serialized_value = json.dumps(value)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def get_or_set(self, key: str, default_func: Callable, ttl: Optional[int] = None) -> Any:
        """
        Get value from cache or set it using a function.
        
        Args:
            key: Cache key
            default_func: Function to call if key doesn't exist
            ttl: Time to live in seconds
            
        Returns:
            Cached value or result of default_func
        """
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Get fresh value
        fresh_value = default_func()
        self.set(key, fresh_value, ttl)
        return fresh_value
    
    def invalidate_user_cache(self, user_id: int) -> bool:
        """
        Invalidate all cache entries for a specific user.
        
        Args:
            user_id: User ID to invalidate cache for
            
        Returns:
            True if successful, False otherwise
        """
        patterns = [
            f"user:{user_id}:*",
            f"messages:{user_id}:*",
            f"stats:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.delete_pattern(pattern)
        
        logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")
        return total_deleted > 0

# Global cache instance
cache_manager = CacheManager()

def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        
    Example:
        @cached(ttl=300, key_prefix="user")
        def get_user_by_id(user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

def cache_invalidate(pattern: str):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        pattern: Cache key pattern to invalidate
        
    Example:
        @cache_invalidate("user:*")
        def update_user(user_id: int, data: dict):
            # Update user logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cache_manager.delete_pattern(pattern)
            return result
        
        return wrapper
    return decorator 