from logging import getLogger
from fastapi import FastAPI, HTTPException, Depends, status, APIRouter, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import timedelta
from sqlalchemy.orm import Session
from typing import List
from auth import create_access_token, authenticate_user, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash
from database import get_db, engine
from services import ChatService
import models, schemas, chatbot
from models import Base

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Create separate routers
message_router = APIRouter(prefix="/messages", tags=["messages"])
user_router = APIRouter(prefix="/users", tags=["users"])

logger = getLogger(__name__)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

# Message routes
@message_router.post("/", response_model=schemas.MessageResponse)
def send_message(message: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_message, new_reply = ChatService.create_message(db, current_user.id, message.content)

    return schemas.MessageResponse(
        message=schemas.Message.model_validate(new_message),
        reply=schemas.Message.model_validate(new_reply),
    )

@message_router.delete("/{message_id}", response_model=schemas.Message)
def delete_message(message_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    message = ChatService.delete_message(db, current_user.id, message_id)
    return schemas.Message.model_validate(message)

@message_router.put("/{message_id}", response_model=schemas.MessageResponse)
def edit_message(
    message_id: int,
    message_update: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    message, reply = ChatService.edit_message_and_update_reply(
        db,
        current_user.id,
        message_id,
        message_update.content
    )
    return schemas.MessageResponse(
        message=schemas.Message.model_validate(message),
        reply=schemas.Message.model_validate(reply),
    )

@message_router.get("/history", response_model=List[schemas.Message])
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    messages = ChatService.get_messages_paginated(db, current_user.id, skip=skip, limit=limit)
    return messages

# User routes
@user_router.post("/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    new_user = ChatService.create_new_user(db, user)
    return new_user

@user_router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    logger.info(f"User {current_user.username} is currently logged in")
    return current_user

# Authentication routes
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    token = ChatService.authenticate_and_create_token(db, username, password)
    return token

# Include routers
app.include_router(message_router, dependencies=[Depends(get_current_user)])
app.include_router(user_router)