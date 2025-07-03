from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from core.auth import get_current_user
from database import get_db
from services.chat import ChatService
from services.user import UserService
from core.config import PAGINATION_DEFAULT_LIMIT, PAGINATION_MAX_LIMIT
import models, schemas

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=schemas.MessageResponse)
def send_message(
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Send a message and get a chatbot reply."""
    user_message, chatbot_reply = ChatService.create_message(db, current_user["id"], message.content)
    
    return schemas.MessageResponse(
        message=schemas.Message.from_orm(user_message),
        reply=schemas.Message.from_orm(chatbot_reply)
    )

@router.get("/", response_model=schemas.MessageListResponse)
def get_messages(
    skip: int = Query(0, ge=0, description="Number of messages to skip"),
    limit: int = Query(PAGINATION_DEFAULT_LIMIT, ge=1, le=PAGINATION_MAX_LIMIT, description="Number of messages to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated messages for the current user."""
    messages, total_count = ChatService.get_messages_paginated(db, current_user["id"], skip, limit)
    
    return schemas.MessageListResponse(
        messages=[schemas.Message.from_orm(msg) for msg in messages],
        total=total_count,
        skip=skip,
        limit=limit
    )

@router.get("/search", response_model=schemas.MessageListResponse)
def search_messages(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search messages by content."""
    messages = ChatService.search_messages(db, current_user["id"], q, limit)
    
    return schemas.MessageListResponse(
        messages=[schemas.Message.from_orm(msg) for msg in messages],
        total=len(messages),
        skip=0,
        limit=limit
    )

@router.get("/conversations", response_model=schemas.ConversationListResponse)
def get_recent_conversations(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of conversations"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get recent conversations for the current user."""
    conversations = ChatService.get_recent_conversations(db, current_user["id"], limit)
    
    return schemas.ConversationListResponse(
        conversations=conversations,
        total=len(conversations)
    )

@router.get("/{message_id}/context", response_model=schemas.MessageContextResponse)
def get_message_context(
    message_id: int,
    context_size: int = Query(2, ge=0, le=10, description="Number of messages before and after"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a message with surrounding context."""
    context_data = ChatService.get_message_with_context(db, message_id, context_size)
    
    if not context_data:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return schemas.MessageContextResponse(**context_data)

@router.put("/{message_id}", response_model=schemas.MessageResponse)
def edit_message(
    message_id: int,
    message_update: schemas.MessageUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Edit a message and update its chatbot reply."""
    user_message, chatbot_reply = ChatService.edit_message_and_update_reply(
        db, current_user["id"], message_id, message_update.content
    )
    
    return schemas.MessageResponse(
        message=schemas.Message.from_orm(user_message),
        reply=schemas.Message.from_orm(chatbot_reply)
    )

@router.delete("/{message_id}", response_model=schemas.Message)
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a message and its associated reply."""
    message = ChatService.delete_message(db, current_user["id"], message_id)
    return schemas.Message.from_orm(message)

@router.get("/history", response_model=List[schemas.Message])
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    messages = ChatService.get_messages_paginated(db, current_user.id, skip=skip, limit=limit)
    return messages 