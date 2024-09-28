from pydantic import BaseModel
from typing import Optional

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    user_id: int
    is_from_user: bool
    reply_to: Optional[int] = None

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: Message
    reply: Message

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
