from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyHeader
from datetime import timedelta
from typing import Optional
from jose import JWTError, jwt

from api.models.user import Token, TokenData, UserCreate, UserResponse, UserUpdate, APIKeyCreate, APIKeyResponse
from api.services.auth import authenticate_user, create_access_token, create_api_key
from api.repositories.user_repository import get_user_repository
from api.config.settings import get_settings
from api.dependencies.auth import check_user_access

settings = get_settings()
router = APIRouter()

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user_or_api_key(
    token: str = Depends(oauth2_scheme),
    api_key: Optional[str] = Security(api_key_header),
    user_repo = Depends(get_user_repository)
):
    """Try JWT auth first, then API key auth. Raise 401 if neither works."""
    try:
        if token:
            return await get_current_user(token=token, user_repo=user_repo)
    except Exception:
        pass
    if api_key:
        user = await get_user_from_api_key(api_key=api_key, user_repo=user_repo)
        if user:
            return user
    raise HTTPException(status_code=401, detail="Not authenticated. Provide a valid Bearer token or X-API-Key.")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo = Depends(get_user_repository)
):
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = await user_repo.get_user_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Add is_admin to user data
    user_dict = user.dict()
    user_dict["is_admin"] = user.is_admin
    return user_dict

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get the current active user."""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(current_user = Depends(get_current_user)):
    """Get the current user if they are an admin."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
    return current_user

async def get_user_from_api_key(
    api_key: Optional[str] = Security(api_key_header),
    user_repo = Depends(get_user_repository)
):
    """Get the user from API key."""
    if api_key is None:
        return None
    
    user_id = await user_repo.verify_api_key(api_key)
    if not user_id:
        return None
    
    return await user_repo.get_user_by_id(user_id)

# Authentication endpoints
@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, user_repo = Depends(get_user_repository)):
    """Register a new user."""
    db_user = await user_repo.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = await user_repo.get_user_by_username(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    return await user_repo.create_user(user)

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo = Depends(get_user_repository)
):
    """Get an access token using username and password."""
    user = await authenticate_user(user_repo, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key_endpoint(
    key_data: APIKeyCreate,
    current_user = Depends(get_current_active_user),
    user_repo = Depends(get_user_repository)
):
    """Create a new API key for the current user."""
    api_key = create_api_key()
    
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    return await user_repo.create_api_key(
        user_id=current_user.id,
        key_name=key_data.key_name,
        api_key=api_key,
        expires_at=expires_at
    )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_active_user)):
    """Get information about the current authenticated user."""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_update: UserUpdate,
    current_user = Depends(get_current_active_user),
    user_repo = Depends(get_user_repository)
):
    """Update the current user's information."""
    return await user_repo.update_user(current_user.id, user_update)
