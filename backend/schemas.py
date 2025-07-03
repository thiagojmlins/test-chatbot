from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# Base Models
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordUpdate(BaseModel):
    new_password: str

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class MessageUpdate(MessageBase):
    pass

# Response Models
class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    created_at: datetime
    updated_at: datetime

class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    content: str
    is_from_user: bool
    reply_to: Optional[int] = None
    user_id: int
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    message: Message
    reply: Message

class MessageListResponse(BaseModel):
    messages: List[Message]
    total: int
    skip: int
    limit: int

class ConversationItem(BaseModel):
    id: int
    user_message: str
    bot_reply: Optional[str] = None
    created_at: str
    has_reply: bool

class ConversationListResponse(BaseModel):
    conversations: List[ConversationItem]
    total: int

class MessageContextItem(BaseModel):
    id: int
    content: str
    is_from_user: bool
    created_at: str

class MessageContextResponse(BaseModel):
    target_message: MessageContextItem
    context: List[MessageContextItem]

class UserStats(BaseModel):
    total_messages: int
    user_messages: int
    bot_messages: int
    conversations: int
    last_message_at: Optional[str] = None

class DailyActivity(BaseModel):
    date: str
    message_count: int

class UserActivity(BaseModel):
    period_days: int
    start_date: str
    end_date: str
    total_messages: int
    user_messages: int
    bot_messages: int
    daily_activity: List[DailyActivity]
    average_messages_per_day: float

class UserListResponse(BaseModel):
    users: List[User]
    total: int
    skip: int
    limit: int

class Token(BaseModel):
    access_token: str
    token_type: str

# Legacy Models (for backward compatibility)
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
