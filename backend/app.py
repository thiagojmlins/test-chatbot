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
    # Simulate chatbot reply
    reply_content = chatbot.generate_reply(new_message.content)
    new_reply = models.Message(content=reply_content, reply_to=new_message.id)
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)

    return schemas.MessageResponse(message=schemas.Message.model_validate(new_message), reply=schemas.Message.model_validate(new_reply))

@app.delete("/delete_message/{message_id}", response_model=schemas.Message)
def delete_message(message_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()
    return schemas.Message.model_validate(message)

@app.put("/edit_message/{message_id}", response_model=schemas.MessageResponse)
def edit_message(message_id: int, message_update: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.content = message_update.content
    db.commit()
    db.refresh(message)

    # Simulate chatbot new reply
    new_reply_content = chatbot.generate_reply(message.content)
    new_reply = db.query(models.Message).filter(models.Message.reply_to == message_id).first()
    if new_reply:
        new_reply.content = new_reply_content
        db.commit()
        db.refresh(new_reply)
    else:
        new_reply = models.Message(content=new_reply_content, reply_to=message_id)
        db.add(new_reply)
        db.commit()
        db.refresh(new_reply)

    return schemas.MessageResponse(message=schemas.Message.model_validate(message), reply=schemas.Message.model_validate(new_reply))

@app.get("/history", response_model=List[schemas.Message])
def get_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    messages = db.query(models.Message).all()
    return messages

# Authentication-related routes

# Create a user (signup)
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Get token (login)
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
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

# Protected endpoint
@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

app.include_router(router, dependencies=[Depends(get_current_user)])