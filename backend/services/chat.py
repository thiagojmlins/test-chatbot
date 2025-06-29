from sqlalchemy.orm import Session
from fastapi import HTTPException
import models, chatbot

class ChatService:
    @staticmethod
    def create_message(db: Session, user_id: int, content: str):
        user_message = models.Message(
            user_id=user_id,
            content=content,
            is_from_user=True
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        reply_content = chatbot.generate_reply(content)
        chatbot_reply = models.Message(
            user_id=user_id,
            content=reply_content,
            is_from_user=False,
            reply_to=user_message.id
        )
        db.add(chatbot_reply)
        db.commit()
        db.refresh(chatbot_reply)

        return user_message, chatbot_reply

    @staticmethod
    def delete_message(db: Session, user_id: int, message_id: int):
        message = db.query(models.Message).filter(models.Message.id == message_id, models.Message.user_id == user_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        db.query(models.Message).filter(models.Message.reply_to == message_id).delete()
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
        messages = db.query(models.Message).filter(models.Message.user_id == user_id).order_by((models.Message.id)).offset(skip).limit(limit).all()
        return messages 