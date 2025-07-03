from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from core.cache import cache_manager, cached, cache_invalidate
from core.config import PAGINATION_DEFAULT_LIMIT, PAGINATION_MAX_LIMIT
import models

class QueryService:
    """Optimized query service with caching and performance improvements."""
    
    @staticmethod
    @cached(ttl=300, key_prefix="user")
    def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
        """
        Get user by ID with caching.
        
        Args:
            db: Database session
            user_id: User ID to retrieve
            
        Returns:
            User object or None if not found
        """
        return db.query(models.User).filter(models.User.id == user_id).first()
    
    @staticmethod
    @cached(ttl=300, key_prefix="user")
    def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
        """
        Get user by username with caching.
        
        Args:
            db: Database session
            username: Username to search for
            
        Returns:
            User object or None if not found
        """
        return db.query(models.User).filter(models.User.username == username).first()
    
    @staticmethod
    def get_messages_paginated_optimized(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = PAGINATION_DEFAULT_LIMIT,
        include_replies: bool = True
    ) -> Tuple[List[models.Message], int]:
        """
        Get paginated messages with optimized querying and caching.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of messages to skip
            limit: Maximum number of messages to return
            include_replies: Whether to include reply messages
            
        Returns:
            Tuple of (messages, total_count)
        """
        # Validate pagination parameters
        limit = min(limit, PAGINATION_MAX_LIMIT)
        skip = max(0, skip)
        
        # Build query with optimizations
        query = db.query(models.Message).filter(
            models.Message.user_id == user_id
        )
        
        if include_replies:
            # Use eager loading for replies
            query = query.options(
                joinedload(models.Message.replies)
            )
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        messages = query.order_by(
            desc(models.Message.created_at)
        ).offset(skip).limit(limit).all()
        
        return messages, total_count
    
    @staticmethod
    @cached(ttl=180, key_prefix="stats")
    def get_user_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get user statistics with caching.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with user statistics
        """
        # Use optimized queries with aggregation
        stats = db.query(
            func.count(models.Message.id).label('total_messages'),
            func.count(models.Message.id).filter(models.Message.is_from_user == True).label('user_messages'),
            func.count(models.Message.id).filter(models.Message.is_from_user == False).label('bot_messages'),
            func.max(models.Message.created_at).label('last_message_at')
        ).filter(models.Message.user_id == user_id).first()
        
        return {
            "total_messages": stats.total_messages or 0,
            "user_messages": stats.user_messages or 0,
            "bot_messages": stats.bot_messages or 0,
            "conversations": stats.user_messages or 0,
            "last_message_at": stats.last_message_at.isoformat() if stats.last_message_at else None
        }
    
    @staticmethod
    def search_messages_optimized(
        db: Session, 
        user_id: int, 
        search_term: str, 
        limit: int = 20
    ) -> List[models.Message]:
        """
        Search messages with optimized full-text search.
        
        Args:
            db: Database session
            user_id: User ID
            search_term: Term to search for
            limit: Maximum number of results
            
        Returns:
            List of matching messages
        """
        # Use ILIKE for case-insensitive search with optimization
        search_pattern = f"%{search_term}%"
        
        return db.query(models.Message).filter(
            and_(
                models.Message.user_id == user_id,
                models.Message.content.ilike(search_pattern)
            )
        ).order_by(
            desc(models.Message.created_at)
        ).limit(limit).all()
    
    @staticmethod
    def get_recent_conversations(
        db: Session, 
        user_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversations with optimized querying.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of conversations
            
        Returns:
            List of recent conversations
        """
        # Get user messages with their replies
        user_messages = db.query(models.Message).filter(
            and_(
                models.Message.user_id == user_id,
                models.Message.is_from_user == True
            )
        ).options(
            joinedload(models.Message.replies)
        ).order_by(
            desc(models.Message.created_at)
        ).limit(limit).all()
        
        conversations = []
        for message in user_messages:
            reply = message.replies[0] if message.replies else None
            conversations.append({
                "id": message.id,
                "user_message": message.content,
                "bot_reply": reply.content if reply else None,
                "created_at": message.created_at.isoformat(),
                "has_reply": reply is not None
            })
        
        return conversations
    
    @staticmethod
    def get_message_with_context(
        db: Session, 
        message_id: int, 
        context_size: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Get a message with surrounding context.
        
        Args:
            db: Database session
            message_id: Message ID
            context_size: Number of messages before and after
            
        Returns:
            Message with context or None if not found
        """
        # Get the target message
        target_message = db.query(models.Message).filter(
            models.Message.id == message_id
        ).first()
        
        if not target_message:
            return None
        
        # Get context messages
        context_messages = db.query(models.Message).filter(
            and_(
                models.Message.user_id == target_message.user_id,
                models.Message.id.between(
                    target_message.id - context_size,
                    target_message.id + context_size
                )
            )
        ).order_by(models.Message.id).all()
        
        return {
            "target_message": {
                "id": target_message.id,
                "content": target_message.content,
                "is_from_user": target_message.is_from_user,
                "created_at": target_message.created_at.isoformat()
            },
            "context": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "is_from_user": msg.is_from_user,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in context_messages
            ]
        }
    
    @staticmethod
    def get_user_activity_summary(
        db: Session, 
        user_id: int, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get user activity summary for the last N days.
        
        Args:
            db: Database session
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Activity summary dictionary
        """
        from datetime import datetime, timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily message counts
        daily_stats = db.query(
            func.date(models.Message.created_at).label('date'),
            func.count(models.Message.id).label('count')
        ).filter(
            and_(
                models.Message.user_id == user_id,
                models.Message.created_at >= start_date,
                models.Message.created_at <= end_date
            )
        ).group_by(
            func.date(models.Message.created_at)
        ).order_by(
            func.date(models.Message.created_at)
        ).all()
        
        # Get total stats for the period
        total_stats = db.query(
            func.count(models.Message.id).label('total_messages'),
            func.count(models.Message.id).filter(models.Message.is_from_user == True).label('user_messages'),
            func.count(models.Message.id).filter(models.Message.is_from_user == False).label('bot_messages')
        ).filter(
            and_(
                models.Message.user_id == user_id,
                models.Message.created_at >= start_date,
                models.Message.created_at <= end_date
            )
        ).first()
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_messages": total_stats.total_messages or 0,
            "user_messages": total_stats.user_messages or 0,
            "bot_messages": total_stats.bot_messages or 0,
            "daily_activity": [
                {
                    "date": stat.date.isoformat(),
                    "message_count": stat.count
                }
                for stat in daily_stats
            ],
            "average_messages_per_day": round(
                (total_stats.total_messages or 0) / days, 2
            )
        }
    
    @staticmethod
    @cache_invalidate("user:*")
    def invalidate_user_cache(user_id: int) -> bool:
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User ID to invalidate cache for
            
        Returns:
            True if successful, False otherwise
        """
        return cache_manager.invalidate_user_cache(user_id) 