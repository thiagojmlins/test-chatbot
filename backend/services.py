from sqlalchemy import desc
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

class ChatService:
    @staticmethod
    def create_message(db: Session, content: str, user_id: int):
        new_message = models.Message(user_id=user_id, content=content, is_from_user=True)
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return new_message

    @staticmethod
    def create_reply(db: Session, user_id: int, message_content: str, reply_to_id: int):
        reply_content = chatbot.generate_reply(message_content)
        new_reply = models.Message(user_id=user_id, content=reply_content, reply_to=reply_to_id, is_from_user=False)
        db.add(new_reply)
        db.commit()
        db.refresh(new_reply)
        return new_reply

    @staticmethod
    def delete_message(db: Session, user_id: int, message_id: int):
        message = db.query(models.Message).filter(models.Message.id == message_id, models.Message.user_id == user_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        db.delete(message)
        db.commit()
        return message

    @staticmethod
    def edit_message_and_update_reply(db: Session, user_id: int, message_id: int, new_content: str):
        message = db.query(models.Message).filter(models.Message.id == message_id, models.Message.user_id == user_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        message.content = new_content
        db.commit()
        db.refresh(message)

        new_reply_content = chatbot.generate_reply(message.content)
        reply = ChatService.get_message_reply(db, message_id)

        if reply:
            reply.content = new_reply_content
            db.commit()
            db.refresh(reply)
        else:
            reply = ChatService.create_reply(db, new_reply_content, message_id)

        return message, reply

    @staticmethod
    def get_message_reply(db: Session, message_id: int):
        reply = db.query(models.Message).filter(models.Message.reply_to == message_id).first()
        return reply

    @staticmethod
    def get_messages_paginated(db: Session, user_id: int, skip: int = 0, limit: int = 10):
        messages = db.query(models.Message).filter(models.Message.user_id == user_id).order_by(desc(models.Message.id)).offset(skip).limit(limit).all()
        return messages

    @staticmethod
    def create_new_user(db: Session, user: schemas.UserCreate):
        db_user = db.query(models.User).filter(models.User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_password = get_password_hash(user.password)
        new_user = models.User(username=user.username, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_and_create_token(db: Session, username: str, password: str):
        user = authenticate_user(db, username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}