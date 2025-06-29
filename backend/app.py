from logging import getLogger
from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.auth import get_current_user
from database import get_db, engine
from services.auth import AuthService
from routers.messages import router as message_router
from routers.users import router as user_router
import models, schemas
from models import Base

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

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

# Authentication route
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    token = AuthService.authenticate_and_create_token(db, username, password)
    return token

# Include routers
app.include_router(message_router, dependencies=[Depends(get_current_user)])
app.include_router(user_router)