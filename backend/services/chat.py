from sqlalchemy.orm import Session
from core.exceptions import MessageNotFoundError, ChatbotServiceError
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

        try:
            reply_content = chatbot.generate_reply(content)
        except Exception as e:
            raise ChatbotServiceError(f"Failed to generate reply: {str(e)}")

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
            raise MessageNotFoundError(message_id)
        
        db.query(models.Message).filter(models.Message.reply_to == message_id).delete()
        db.delete(message)
        db.commit()
        return message

    @staticmethod
    def edit_message_and_update_reply(db: Session, user_id: int, message_id: int, new_content: str):
        message = db.query(models.Message).filter(models.Message.id == message_id, models.Message.user_id == user_id).first()
        if not message:
            raise MessageNotFoundError(message_id)
        
        message.content = new_content
        db.commit()
        db.refresh(message)
        
        try:
            new_reply_content = chatbot.generate_reply(message.content)
        except Exception as e:
            raise ChatbotServiceError(f"Failed to generate reply: {str(e)}")
        
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

    @staticmethod
    def create_reply(db: Session, content: str, message_id: int):
        """Create a reply to a message."""
        reply = models.Message(
            user_id=db.query(models.Message).filter(models.Message.id == message_id).first().user_id,
            content=content,
            is_from_user=False,
            reply_to=message_id
        )
        db.add(reply)
        db.commit()
        db.refresh(reply)
        return reply 