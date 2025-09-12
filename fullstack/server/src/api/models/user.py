from typing import Optional
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)


class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int