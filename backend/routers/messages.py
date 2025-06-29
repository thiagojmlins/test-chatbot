from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from core.auth import get_current_user
from database import get_db
from services.chat import ChatService
import models, schemas

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=schemas.MessageResponse)
def send_message(message: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_message, new_reply = ChatService.create_message(db, current_user.id, message.content)
    return schemas.MessageResponse(
        message=schemas.Message.model_validate(new_message),
        reply=schemas.Message.model_validate(new_reply),
    )

@router.delete("/{message_id}", response_model=schemas.Message)
def delete_message(message_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    message = ChatService.delete_message(db, current_user.id, message_id)
    return schemas.Message.model_validate(message)

@router.put("/{message_id}", response_model=schemas.MessageResponse)
def edit_message(
    message_id: int,
    message_update: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    message, reply = ChatService.edit_message_and_update_reply(
        db,
        current_user.id,
        message_id,
        message_update.content
    )
    return schemas.MessageResponse(
        message=schemas.Message.model_validate(message),
        reply=schemas.Message.model_validate(reply),
    )

@router.get("/history", response_model=List[schemas.Message])
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    messages = ChatService.get_messages_paginated(db, current_user.id, skip=skip, limit=limit)
    return messages 