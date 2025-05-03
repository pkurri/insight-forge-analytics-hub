
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from uuid import uuid4

from models.user import TokenData, UserDB
from config.settings import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def authenticate_user(db, username: str, password: str) -> Optional[UserDB]:
    """Authenticate a user by username and password."""
    user = await db.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_api_key() -> str:
    """Generate a unique API key."""
    return f"df_{uuid4().hex}_{uuid4().hex[:8]}"

async def verify_api_key(db, api_key: str) -> Optional[int]:
    """Verify an API key and return the user_id if valid."""
    key_data = await db.get_api_key(api_key)
    if not key_data:
        return None
    
    if not key_data.is_active:
        return None
    
    if key_data.expires_at and key_data.expires_at < datetime.utcnow():
        return None
    
    # Update last used timestamp
    await db.update_api_key_usage(key_data.id)
    return key_data.user_id
