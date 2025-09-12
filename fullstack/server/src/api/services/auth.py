import logging
from datetime import datetime, timedelta
from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from src.api.config import JWT_ALGORITHM, JWT_EXPIRATION_MINUTES, JWT_SECRET_KEY
from src.api.db.session import get_session
from src.api.models.token import TokenData
from src.api.models.user import User
from src.api.services.security import verify_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.api.config import API_PREFIX
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/auth/token")


def authenticate_user(session: Session, username: str, password: str) -> Optional[User]:
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        logger.error("JWT token validation error")
        raise credentials_exception
    
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        logger.error(f"User not found: {token_data.username}")
        raise credentials_exception
    return user