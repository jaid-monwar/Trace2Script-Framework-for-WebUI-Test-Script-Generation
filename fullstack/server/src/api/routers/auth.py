import logging
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from src.api.config import JWT_EXPIRATION_MINUTES
from src.api.db.session import get_session
from src.api.models.token import Token
from src.api.models.user import User
from src.api.services.auth import authenticate_user, create_access_token, get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Any:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=JWT_EXPIRATION_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    
    logger.info(f"User authenticated successfully: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    return {
        "username": current_user.username,
        "user_id": current_user.id,
    }