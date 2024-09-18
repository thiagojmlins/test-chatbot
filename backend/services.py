from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import models, schemas, chatbot
from datetime import timedelta
from auth import (
    create_access_token,
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
)

def create_message(db: Session, message: schemas.MessageCreate):
    new_message = models.Message(content=message.content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

def create_reply(db: Session, message_content: str, reply_to_id: int):
    reply_content = chatbot.generate_reply(message_content)
    new_reply = models.Message(content=reply_content, reply_to=reply_to_id)
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    return new_reply