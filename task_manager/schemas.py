from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"
    priority: Optional[int] = 1


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: int
    created_at: datetime
    owner_id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
