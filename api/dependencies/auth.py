"""Authentication Dependencies Module

This module provides dependency injection functions for authentication used in the API.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional
import jwt
from datetime import datetime, timedelta

from api.config.settings import get_settings

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Dependency for getting the current authenticated user.
    
    Args:
        token: JWT token from OAuth2 scheme
        
    Returns:
        Dictionary containing user information
        
    Raises:
        HTTPException: If authentication fails
    """
    # For development, allow unauthenticated access if AUTH_REQUIRED is False
    if not getattr(settings, "AUTH_REQUIRED", True):
        return {"id": "dev-user", "username": "developer", "role": "admin"}
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Check if token has expired
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user data from payload
        user_data = {
            "id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role", "user"),
            "exp": exp
        }
        
        return user_data
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency for ensuring the current user has admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
