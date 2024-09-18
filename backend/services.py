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

def delete_message_by_id(db: Session, message_id: int):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()
    return message

def update_message(db: Session, message_id: int, content: str):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.content = content
    db.commit()
    db.refresh(message)
    return message

def get_message_reply(db: Session, message_id: int):
    reply = db.query(models.Message).filter(models.Message.reply_to == message_id).first()
    return reply

def get_all_messages(db: Session):
    messages = db.query(models.Message).all()
    return messages