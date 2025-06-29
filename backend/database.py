import logging
from contextlib import contextmanager
from typing import Generator, Optional
import psycopg
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
from core.config import SQLALCHEMY_DATABASE_URL, TESTING

# Configure logging
logger = logging.getLogger(__name__)

# Create engine with connection pooling and optimized settings
def create_database_engine() -> create_engine:
    """Create and configure the database engine with optimized settings."""
    
    # Engine configuration based on environment
    if TESTING:
        # SQLite configuration for testing
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=False,  # Disable SQL logging in tests
            poolclass=None  # No pooling for SQLite
        )
    else:
        # PostgreSQL configuration with connection pooling
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            poolclass=QueuePool,
            pool_size=10,  # Number of connections to maintain
            max_overflow=20,  # Additional connections when pool is full
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,  # Set to True for SQL debugging
            # Performance optimizations
            pool_reset_on_return='commit',  # Reset connection state
            isolation_level='READ_COMMITTED'  # Default isolation level
        )
    
    return engine

# Create the engine
engine = create_database_engine()

# Create session factory with optimized settings
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
)

# Base class for all models
Base = declarative_base()

# Database session dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get a database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        This function automatically handles session cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error in session: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_db_session() as db:
            result = db.execute(text("SELECT 1")).scalar()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error in session: {e}")
        db.rollback()
        raise
    finally:
        db.close()

class DatabaseManager:
    """Database manager for handling complex database operations."""
    
    @staticmethod
    def execute_with_retry(operation, max_retries: int = 3, *args, **kwargs):
        """
        Execute a database operation with retry logic.
        
        Args:
            operation: Function to execute
            max_retries: Maximum number of retry attempts
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            SQLAlchemyError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except OperationalError as e:
                last_exception = e
                logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    continue
            except IntegrityError as e:
                # Don't retry integrity errors (constraint violations)
                logger.error(f"Integrity error: {e}")
                raise
            except SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                raise
        
        raise last_exception
    
    @staticmethod
    def health_check() -> bool:
        """
        Check database connectivity and health.
        
        Returns:
            bool: True if database is healthy, False otherwise
        """
        try:
            with get_db_session() as db:
                # Simple query to test connectivity
                db.execute(text("SELECT 1"))
                return True
        except SQLAlchemyError as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @staticmethod
    def get_connection_info() -> dict:
        """
        Get database connection information.
        
        Returns:
            dict: Connection information including pool status
        """
        pool = engine.pool
        info = {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
        
        # Add invalid count if available (depends on SQLAlchemy version)
        if hasattr(pool, 'invalid'):
            info["invalid"] = pool.invalid()
        else:
            info["invalid"] = 0
            
        return info

# Database event listeners for monitoring and optimization
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure SQLite for better performance in testing."""
    if TESTING:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout for monitoring."""
    logger.debug("Database connection checked out")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection checkin for monitoring."""
    logger.debug("Database connection checked in")

# Initialize database tables
def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

# Cleanup database connections
def close_db():
    """Close all database connections."""
    try:
        engine.dispose()
        logger.info("Database connections closed successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error closing database connections: {e}")
        raise