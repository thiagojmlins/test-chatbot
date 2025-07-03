from typing import Tuple, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from core.exceptions import MessageNotFoundError, ChatbotServiceError
import models, chatbot
from database import DatabaseManager
from core.cache import cache_invalidate
from services.query import QueryService
from core.config import PAGINATION_DEFAULT_LIMIT, PAGINATION_MAX_LIMIT

class ChatService:
    """Service for handling chat operations with improved database management and caching."""
    
    @staticmethod
    @cache_invalidate("messages:*")
    def create_message(db: Session, user_id: int, content: str) -> Tuple[models.Message, models.Message]:
        """
        Create a user message and generate a chatbot reply.
        
        Args:
            db: Database session
            user_id: ID of the user sending the message
            content: Content of the user message
            
        Returns:
            Tuple of (user_message, chatbot_reply)
            
        Raises:
            ChatbotServiceError: If chatbot reply generation fails
        """
        def _create_message_operation():
            # Create user message
            user_message = models.Message(
                user_id=user_id,
                content=content,
                is_from_user=True
            )
            db.add(user_message)
            db.flush()  # Get the ID without committing
            
            # Generate chatbot reply
            try:
                reply_content = chatbot.generate_reply(content)
            except Exception as e:
                db.rollback()
                raise ChatbotServiceError(f"Failed to generate reply: {str(e)}")
            
            # Create chatbot reply
            chatbot_reply = models.Message(
                user_id=user_id,
                content=reply_content,
                is_from_user=False,
                reply_to=user_message.id
            )
            db.add(chatbot_reply)
            db.flush()  # Get the ID without committing
            
            # Refresh both objects to get their IDs
            db.refresh(user_message)
            db.refresh(chatbot_reply)
            
            return user_message, chatbot_reply
        
        return DatabaseManager.execute_with_retry(_create_message_operation)

    @staticmethod
    @cache_invalidate("messages:*")
    def delete_message(db: Session, user_id: int, message_id: int) -> models.Message:
        """
        Delete a message and its associated reply.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the message
            message_id: ID of the message to delete
            
        Returns:
            The deleted message
            
        Raises:
            MessageNotFoundError: If message is not found or doesn't belong to user
        """
        def _delete_message_operation():
            # Get the message with user validation
            message = db.query(models.Message).filter(
                models.Message.id == message_id,
                models.Message.user_id == user_id
            ).first()
            
            if not message:
                raise MessageNotFoundError(message_id)
            
            # Delete associated replies first (cascade delete)
            db.query(models.Message).filter(
                models.Message.reply_to == message_id
            ).delete()
            
            # Delete the main message
            db.delete(message)
            db.flush()
            
            return message
        
        return DatabaseManager.execute_with_retry(_delete_message_operation)

    @staticmethod
    @cache_invalidate("messages:*")
    def edit_message_and_update_reply(db: Session, user_id: int, message_id: int, new_content: str) -> Tuple[models.Message, models.Message]:
        """
        Edit a message and update its chatbot reply.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the message
            message_id: ID of the message to edit
            new_content: New content for the message
            
        Returns:
            Tuple of (updated_message, updated_reply)
            
        Raises:
            MessageNotFoundError: If message is not found or doesn't belong to user
            ChatbotServiceError: If chatbot reply generation fails
        """
        def _edit_message_operation():
            # Get the message with user validation
            message = db.query(models.Message).filter(
                models.Message.id == message_id,
                models.Message.user_id == user_id
            ).first()
            
            if not message:
                raise MessageNotFoundError(message_id)
            
            # Update message content
            message.content = new_content
            db.flush()
            
            # Generate new reply content
            try:
                new_reply_content = chatbot.generate_reply(new_content)
            except Exception as e:
                db.rollback()
                raise ChatbotServiceError(f"Failed to generate reply: {str(e)}")
            
            # Update or create reply
            reply = ChatService.get_message_reply(db, message_id)
            if reply:
                reply.content = new_reply_content
                db.flush()
                db.refresh(reply)
            else:
                reply = ChatService.create_reply(db, new_reply_content, message_id)
            
            db.refresh(message)
            return message, reply
        
        return DatabaseManager.execute_with_retry(_edit_message_operation)

    @staticmethod
    def get_message_reply(db: Session, message_id: int) -> Optional[models.Message]:
        """
        Get the reply to a specific message.
        
        Args:
            db: Database session
            message_id: ID of the message to get reply for
            
        Returns:
            The reply message or None if no reply exists
        """
        return db.query(models.Message).filter(
            models.Message.reply_to == message_id
        ).first()

    @staticmethod
    def get_messages_paginated(db: Session, user_id: int, skip: int = 0, limit: int = PAGINATION_DEFAULT_LIMIT) -> Tuple[List[models.Message], int]:
        """
        Get paginated messages for a user with optimized querying.
        
        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of messages to skip
            limit: Maximum number of messages to return
            
        Returns:
            Tuple of (messages, total_count)
        """
        return QueryService.get_messages_paginated_optimized(db, user_id, skip, limit)

    @staticmethod
    def get_messages_with_replies(db: Session, user_id: int, skip: int = 0, limit: int = PAGINATION_DEFAULT_LIMIT) -> List[models.Message]:
        """
        Get paginated messages with their replies using eager loading.
        
        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of messages to skip
            limit: Maximum number of messages to return
            
        Returns:
            List of messages with replies loaded
        """
        return db.query(models.Message).filter(
            models.Message.user_id == user_id,
            models.Message.is_from_user == True  # Only user messages
        ).options(
            joinedload(models.Message.replies)
        ).order_by(models.Message.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def create_reply(db: Session, content: str, message_id: int) -> models.Message:
        """
        Create a reply to a message.
        
        Args:
            db: Database session
            content: Content of the reply
            message_id: ID of the message to reply to
            
        Returns:
            The created reply message
        """
        # Get the original message to get user_id
        original_message = db.query(models.Message).filter(
            models.Message.id == message_id
        ).first()
        
        if not original_message:
            raise MessageNotFoundError(message_id)
        
        reply = models.Message(
            user_id=original_message.user_id,
            content=content,
            is_from_user=False,
            reply_to=message_id
        )
        db.add(reply)
        db.flush()
        db.refresh(reply)
        return reply

    @staticmethod
    def get_message_count(db: Session, user_id: int) -> int:
        """
        Get the total number of messages for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            Total number of messages
        """
        return db.query(models.Message).filter(
            models.Message.user_id == user_id
        ).count()

    @staticmethod
    def search_messages(db: Session, user_id: int, search_term: str, limit: int = 20) -> List[models.Message]:
        """
        Search messages by content for a specific user with optimization.
        
        Args:
            db: Database session
            user_id: ID of the user
            search_term: Term to search for in message content
            limit: Maximum number of results to return
            
        Returns:
            List of messages matching the search term
        """
        return QueryService.search_messages_optimized(db, user_id, search_term, limit)

    @staticmethod
    def get_recent_conversations(db: Session, user_id: int, limit: int = 10) -> List[dict]:
        """
        Get recent conversations for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of conversations to return
            
        Returns:
            List of recent conversations
        """
        return QueryService.get_recent_conversations(db, user_id, limit)

    @staticmethod
    def get_message_with_context(db: Session, message_id: int, context_size: int = 2) -> Optional[dict]:
        """
        Get a message with surrounding context.
        
        Args:
            db: Database session
            message_id: ID of the message
            context_size: Number of messages before and after
            
        Returns:
            Message with context or None if not found
        """
        return QueryService.get_message_with_context(db, message_id, context_size) 