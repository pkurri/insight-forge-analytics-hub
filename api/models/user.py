
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

from sqlalchemy.orm import relationship

class UserDB(UserBase):
    id: int
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime
    conversations = relationship("Conversation", back_populates="user")
    
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class APIKeyCreate(BaseModel):
    key_name: str
    expires_in_days: Optional[int] = None  # None means no expiration

class APIKeyResponse(BaseModel):
    id: int
    key_name: str
    api_key: str
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        orm_mode = True
