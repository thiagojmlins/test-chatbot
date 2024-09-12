from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    reply_to = Column(Integer, ForeignKey('messages.id'), nullable=True)

    replies = relationship("Message", remote_side=[id])
