import pytest
import time
from sqlalchemy.orm import Session
from database import get_db
from services.user import UserService
from services.chat import ChatService
from services.query import QueryService
from core.cache import cache_manager
import models

class TestPerformance:
    """Test performance optimizations and caching functionality."""
    
    def test_cache_functionality(self, db: Session):
        """Test that caching is working properly."""
        # Create a test user
        from schemas import UserCreate
        user_data = UserCreate(username="perf_test_user", password="testpass123")
        user = UserService.create_new_user(db, user_data)
        
        # Test user caching
        start_time = time.time()
        user1 = QueryService.get_user_by_id(db, user.id)
        first_query_time = time.time() - start_time
        
        start_time = time.time()
        user2 = QueryService.get_user_by_id(db, user.id)
        second_query_time = time.time() - start_time
        
        # Second query should be faster (cached)
        assert user1.id == user2.id
        assert second_query_time < first_query_time
        
        # Test cache invalidation
        cache_manager.delete_pattern("user:*")
        
        start_time = time.time()
        user3 = QueryService.get_user_by_id(db, user.id)
        third_query_time = time.time() - start_time
        
        # Third query should be slower again (cache cleared)
        assert third_query_time > second_query_time
    
    def test_paginated_query_performance(self, db: Session):
        """Test paginated query performance with large datasets."""
        # Create a test user
        from schemas import UserCreate
        user_data = UserCreate(username="perf_paginated_user", password="testpass123")
        user = UserService.create_new_user(db, user_data)
        
        # Create many messages
        for i in range(100):
            ChatService.create_message(db, user.id, f"Test message {i}")
        
        # Test paginated query performance
        start_time = time.time()
        messages, total_count = ChatService.get_messages_paginated(db, user.id, skip=0, limit=20)
        query_time = time.time() - start_time
        
        assert len(messages) == 20
        assert total_count == 200  # 100 user messages + 100 bot replies
        assert query_time < 1.0  # Should be fast
    
    def test_search_performance(self, db: Session):
        """Test search query performance."""
        # Create a test user
        from schemas import UserCreate
        user_data = UserCreate(username="perf_search_user", password="testpass123")
        user = UserService.create_new_user(db, user_data)
        
        # Create messages with specific content
        for i in range(50):
            ChatService.create_message(db, user.id, f"Important message {i} with keyword")
        
        # Test search performance
        start_time = time.time()
        results = ChatService.search_messages(db, user.id, "keyword", limit=20)
        search_time = time.time() - start_time
        
        assert len(results) > 0
        assert search_time < 0.5  # Should be fast
    
    def test_stats_query_performance(self, db: Session):
        """Test user statistics query performance."""
        # Create a test user
        from schemas import UserCreate
        user_data = UserCreate(username="perf_stats_user", password="testpass123")
        user = UserService.create_new_user(db, user_data)
        
        # Create messages
        for i in range(50):
            ChatService.create_message(db, user.id, f"Stats test message {i}")
        
        # Test stats query performance
        start_time = time.time()
        stats = UserService.get_user_stats(db, user.id)
        stats_time = time.time() - start_time
        
        assert stats["total_messages"] == 100  # 50 user + 50 bot
        assert stats["user_messages"] == 50
        assert stats["bot_messages"] == 50
        assert stats_time < 0.5  # Should be fast
    
    def test_conversations_query_performance(self, db: Session):
        """Test recent conversations query performance."""
        # Create a test user
        from schemas import UserCreate
        user_data = UserCreate(username="perf_conv_user", password="testpass123")
        user = UserService.create_new_user(db, user_data)
        
        # Create conversations
        for i in range(30):
            ChatService.create_message(db, user.id, f"Conversation {i}")
        
        # Test conversations query performance
        start_time = time.time()
        conversations = ChatService.get_recent_conversations(db, user.id, limit=10)
        conv_time = time.time() - start_time
        
        assert len(conversations) == 10
        assert conv_time < 0.5  # Should be fast
    
    def test_activity_summary_performance(self, db: Session):
        """Test user activity summary performance."""
        # Create a test user
        from schemas import UserCreate
        user_data = UserCreate(username="perf_activity_user", password="testpass123")
        user = UserService.create_new_user(db, user_data)
        
        # Create messages
        for i in range(25):
            ChatService.create_message(db, user.id, f"Activity test message {i}")
        
        # Test activity summary performance
        start_time = time.time()
        activity = UserService.get_user_activity_summary(db, user.id, days=30)
        activity_time = time.time() - start_time
        
        assert activity["total_messages"] == 50  # 25 user + 25 bot
        assert activity["period_days"] == 30
        assert activity_time < 1.0  # Should be reasonable
    
    def test_cache_invalidation(self, db: Session):
        """Test that cache invalidation works properly."""
        # Create a test user
        from schemas import UserCreate
        user_data = UserCreate(username="perf_invalidate_user", password="testpass123")
        user = UserService.create_new_user(db, user_data)
        
        # Get user (should cache)
        user1 = QueryService.get_user_by_id(db, user.id)
        
        # Update user (should invalidate cache)
        UserService.update_user_password(db, user.id, "newpassword123")
        
        # Get user again (should be fresh from DB)
        user2 = QueryService.get_user_by_id(db, user.id)
        
        assert user1.id == user2.id
        # The updated_at timestamp should be different
        assert user2.updated_at > user1.updated_at
    
    def test_database_indexes(self, db: Session):
        """Test that database indexes are working properly."""
        # Create a test user
        from schemas import UserCreate
        user_data = UserCreate(username="perf_index_user", password="testpass123")
        user = UserService.create_new_user(db, user_data)
        
        # Create messages
        for i in range(100):
            ChatService.create_message(db, user.id, f"Index test message {i}")
        
        # Test queries that should use indexes
        start_time = time.time()
        
        # Query by user_id (should use index)
        messages = db.query(models.Message).filter(
            models.Message.user_id == user.id
        ).order_by(models.Message.created_at.desc()).limit(10).all()
        
        query_time = time.time() - start_time
        
        assert len(messages) == 10
        assert query_time < 0.1  # Should be very fast with indexes
    
    def test_connection_pool_performance(self, db: Session):
        """Test database connection pool performance."""
        # Test multiple concurrent-like operations
        start_time = time.time()
        
        for i in range(10):
            # Simulate concurrent operations
            user_data = UserCreate(username=f"pool_test_user_{i}", password="testpass123")
            user = UserService.create_new_user(db, user_data)
            
            # Create some messages
            for j in range(5):
                ChatService.create_message(db, user.id, f"Pool test message {j}")
        
        total_time = time.time() - start_time
        
        # Should handle multiple operations efficiently
        assert total_time < 5.0  # Should be reasonable for 50 operations
    
    def test_memory_usage(self, db: Session):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create a test user
        from schemas import UserCreate
        user_data = UserCreate(username="perf_memory_user", password="testpass123")
        user = UserService.create_new_user(db, user_data)
        
        # Create many messages
        for i in range(1000):
            ChatService.create_message(db, user.id, f"Memory test message {i}")
        
        # Get messages in batches to test memory efficiency
        for skip in range(0, 1000, 100):
            messages, _ = ChatService.get_messages_paginated(db, user.id, skip=skip, limit=100)
            assert len(messages) == 100
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB 