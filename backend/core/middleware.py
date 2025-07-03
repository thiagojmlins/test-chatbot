import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.cache import cache_manager

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring API performance and caching statistics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Track request
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Cache-Enabled"] = str(cache_manager.enabled)
        
        # Log performance metrics
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.4f}s "
            f"- Cache: {'enabled' if cache_manager.enabled else 'disabled'}"
        )
        
        # Log slow requests
        if process_time > 1.0:  # Log requests taking more than 1 second
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {process_time:.4f}s"
            )
        
        return response

class DatabasePerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring database query performance."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # This middleware can be extended to track database query times
        # by integrating with SQLAlchemy event listeners
        
        response = await call_next(request)
        
        # Add database performance headers if available
        # response.headers["X-DB-Queries"] = str(query_count)
        # response.headers["X-DB-Time"] = str(db_time)
        
        return response

class CachePerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring cache performance."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Track cache statistics
        cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0
        }
        
        # Store cache stats in request state
        request.state.cache_stats = cache_stats
        
        response = await call_next(request)
        
        # Add cache performance headers
        if hasattr(request.state, 'cache_stats'):
            stats = request.state.cache_stats
            response.headers["X-Cache-Hits"] = str(stats["hits"])
            response.headers["X-Cache-Misses"] = str(stats["misses"])
            response.headers["X-Cache-Sets"] = str(stats["sets"])
        
        return response

def setup_performance_middleware(app):
    """Setup all performance monitoring middleware."""
    app.add_middleware(PerformanceMiddleware)
    app.add_middleware(CachePerformanceMiddleware)
    # app.add_middleware(DatabasePerformanceMiddleware)  # Enable when needed 