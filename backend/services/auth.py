from datetime import timedelta
from fastapi import HTTPException, status
from core.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

class AuthService:
    @staticmethod
    def authenticate_and_create_token(db, username: str, password: str):
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