from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal, engine
import models, schemas, chatbot
from models import Base

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/send_message", response_model=schemas.MessageResponse)
def send_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    new_message = models.Message(content=message.content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # Simulate chatbot reply
    reply_content = chatbot.generate_reply(new_message.content)
    new_reply = models.Message(content=reply_content, reply_to=new_message.id)
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)

    return schemas.MessageResponse(message=schemas.Message.model_validate(new_message), reply=schemas.Message.from_orm(new_reply))


@app.delete("/delete_message/{message_id}", response_model=schemas.Message)
def delete_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()
    return schemas.Message.model_validate(message)


@app.put("/edit_message/{message_id}", response_model=schemas.MessageResponse)
def edit_message(message_id: int, message_update: schemas.MessageCreate, db: Session = Depends(get_db)):
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
def get_history(db: Session = Depends(get_db)):
    messages = db.query(models.Message).all()
    return messages
