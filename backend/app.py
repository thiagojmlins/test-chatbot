from logging import getLogger
from fastapi import FastAPI, HTTPException, Depends, status, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from sqlalchemy.orm import Session
from typing import List
from auth import create_access_token, authenticate_user, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash
from database import get_db, engine
import models, schemas, chatbot
from models import Base
import services

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
router = APIRouter()

logger = getLogger(__name__)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/send_message", response_model=schemas.MessageResponse)
def send_message(message: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_message = services.create_message(db, message)
    new_reply = services.create_reply(
      db, new_message.content, new_message.id
    )

    return schemas.MessageResponse(
        message=schemas.Message.model_validate(new_message),
        reply=schemas.Message.model_validate(new_reply),
    )

@app.delete("/delete_message/{message_id}", response_model=schemas.Message)
def delete_message(message_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    message = services.delete_message_by_id(db, message_id)
    return schemas.Message.model_validate(message)

@app.put("/edit_message/{message_id}", response_model=schemas.MessageResponse)
def edit_message(message_id: int, message_update: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    message = services.update_message(db, message_id, message_update.content)
    new_reply_content = chatbot.generate_reply(message.content)
    new_reply = services.get_message_reply(db, message_id)
    if new_reply:
        new_reply.content = new_reply_content
        db.commit()
        db.refresh(new_reply)
    else:
        new_reply = services.create_reply(db, message.content, message_id)
    return schemas.MessageResponse(
        message=schemas.Message.model_validate(message),
        reply=schemas.Message.model_validate(new_reply),
    )

@app.get("/history", response_model=List[schemas.Message])
def get_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    messages = services.get_all_messages(db)
    return messages

# Authentication-related routes

# Create a user (signup)
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    new_user = services.create_new_user(db, user)
    return new_user

# Get token (login)
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    token = services.authenticate_and_create_token(db, username, password)
    return token

# Protected endpoint
@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

app.include_router(router, dependencies=[Depends(get_current_user)])