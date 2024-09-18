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