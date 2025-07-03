from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Index, Text
from sqlalchemy.orm import relationship
from database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    is_from_user = Column(Boolean, nullable=False, index=True)
    reply_to = Column(Integer, ForeignKey('messages.id'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="messages")
    replies = relationship("Message", remote_side=[id], cascade="all, delete-orphan", single_parent=True)

    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for getting user messages with pagination
        Index('idx_messages_user_created', 'user_id', 'created_at'),
        # Index for getting user messages only
        Index('idx_messages_user_from_user', 'user_id', 'is_from_user'),
        # Index for reply lookups
        Index('idx_messages_reply_to', 'reply_to'),
        # Index for content search (if needed)
        Index('idx_messages_content_gin', 'content', postgresql_using='gin'),
    )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")

    # Composite index for username lookups
    __table_args__ = (
        Index('idx_users_username_created', 'username', 'created_at'),
    )
