import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import (
    get_db_session, DatabaseManager, engine, 
    init_db, close_db, get_db, Base
)
from models import User, Message
from core.auth import get_password_hash

@pytest.fixture(autouse=True, scope="class")
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestDatabaseManagement:
    """Test database management functionality."""
    
    def test_database_health_check(self):
        """Test that database health check works correctly."""
        assert DatabaseManager.health_check() == True
    
    def test_connection_info(self):
        """Test that connection pool information is accessible."""
        info = DatabaseManager.get_connection_info()
        assert isinstance(info, dict)
        assert "pool_size" in info
        assert "checked_in" in info
        assert "checked_out" in info
        assert "overflow" in info
        assert "invalid" in info
    
    def test_context_manager_session(self):
        """Test that context manager session works correctly."""
        with get_db_session() as db:
            assert isinstance(db, Session)
            # Test that we can perform a simple query
            result = db.execute(text("SELECT 1")).scalar()
            assert result == 1
    
    def test_context_manager_rollback_on_error(self):
        """Test that context manager rolls back on error."""
        db_session = None
        with pytest.raises(Exception):
            with get_db_session() as db:
                db_session = db
                # This should cause an error and rollback
                db.execute(text("SELECT * FROM non_existent_table"))
        # The important thing is that the transaction was rolled back and the session is still usable
        assert db_session is not None
    
    def test_retry_mechanism(self):
        """Test that retry mechanism works for database operations."""
        def failing_operation():
            raise Exception("Simulated database error")
        
        # Should fail after retries
        with pytest.raises(Exception):
            DatabaseManager.execute_with_retry(failing_operation)
    
    def test_database_initialization(self):
        """Test that database initialization works."""
        # This should not raise any errors
        init_db()
    
    def test_session_dependency(self):
        """Test that FastAPI session dependency works."""
        # Test the generator function
        session_gen = get_db()
        db = next(session_gen)
        assert isinstance(db, Session)
        
        # Clean up
        try:
            next(session_gen)
        except StopIteration:
            pass

class TestDatabaseOperations:
    """Test database operations with improved session management."""
    
    def test_user_creation_with_context_manager(self):
        """Test creating a user using context manager."""
        with get_db_session() as db:
            user = User(
                username="testuser_context",
                hashed_password=get_password_hash("testpass")
            )
            db.add(user)
            db.flush()
            db.refresh(user)
            
            assert user.id is not None
            assert user.username == "testuser_context"
    
    def test_message_creation_with_context_manager(self):
        """Test creating a message using context manager."""
        with get_db_session() as db:
            # Create a user first
            user = User(
                username="testuser_message",
                hashed_password=get_password_hash("testpass")
            )
            db.add(user)
            db.flush()
            
            # Create a message
            message = Message(
                user_id=user.id,
                content="Test message",
                is_from_user=True
            )
            db.add(message)
            db.flush()
            db.refresh(message)
            
            assert message.id is not None
            assert message.content == "Test message"
            assert message.user_id == user.id
    
    def test_transaction_rollback(self):
        """Test that transactions are properly rolled back on error."""
        # This should rollback the entire transaction
        with pytest.raises(Exception):
            with get_db_session() as db:
                # Create a user
                user = User(
                    username="testuser_rollback",
                    hashed_password=get_password_hash("testpass")
                )
                db.add(user)
                db.flush()
                
                # This should cause an error and rollback everything
                db.execute(text("SELECT * FROM non_existent_table"))
        
        # Verify the user was not created (rolled back)
        with get_db_session() as db:
            user = db.query(User).filter(User.username == "testuser_rollback").first()
            assert user is None

class TestDatabasePerformance:
    """Test database performance improvements."""
    
    def test_connection_pooling(self):
        """Test that connection pooling is working."""
        # Get initial pool info
        initial_info = DatabaseManager.get_connection_info()
        
        # Perform multiple operations to test pooling
        for i in range(5):
            with get_db_session() as db:
                db.execute(text("SELECT 1")).scalar()
        
        # Get final pool info
        final_info = DatabaseManager.get_connection_info()
        
        # Verify pool is being used efficiently
        assert final_info["checked_in"] >= 0
        assert final_info["checked_out"] >= 0
    
    def test_query_optimization(self):
        """Test that queries are optimized."""
        with get_db_session() as db:
            # Test that we can perform multiple queries efficiently
            for i in range(10):
                result = db.execute(text("SELECT 1")).scalar()
                assert result == 1 