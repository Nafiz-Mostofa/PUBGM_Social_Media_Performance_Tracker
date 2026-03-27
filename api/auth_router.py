from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from api.security import create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login_for_access_token(request: OAuth2PasswordRequestForm = Depends()):
    # Get hardcoded admin credentials from .env
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")
    
    if not admin_password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin password hash not configured in environment."
        )

    if request.username != admin_username or not verify_password(request.password, admin_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin_username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": admin_username}
