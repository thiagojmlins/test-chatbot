from pydantic import BaseModel
from typing import Optional

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    reply_to: Optional[int] = None

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: Message
    reply: Message
