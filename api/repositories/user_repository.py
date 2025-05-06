from datetime import datetime
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from api.models.user import UserCreate, UserDB, UserUpdate, APIKeyResponse
from api.services.auth import get_password_hash
from api.config.settings import get_settings
from api.db.connection import get_db_session, get_db_pool

settings = get_settings()

class UserRepository:
    def __init__(self, session):
        self.session = session

    async def create_user(self, user: UserCreate) -> UserDB:
        """Create a new user."""
        async with self.pool.acquire() as conn:
            now = datetime.utcnow()
            result = await conn.fetchrow(
                """
                INSERT INTO users (username, email, password_hash, full_name, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $5)
                RETURNING id, username, email, full_name, is_active, is_admin, created_at, updated_at
                """,
                user.username,
                user.email,
                get_password_hash(user.password),
                user.full_name,
                now
            )
            return UserDB(**dict(result))

    async def get_user_by_username(self, username: str) -> Optional[UserDB]:
        """Get user by username."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT id, username, email, password_hash, full_name, is_active, is_admin, created_at, updated_at
                FROM users
                WHERE username = $1
                """,
                username
            )
            if result:
                return UserDB(**dict(result))
            return None

    async def get_user_by_email(self, email: str) -> Optional[UserDB]:
        """Get user by email."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT id, username, email, password_hash, full_name, is_active, is_admin, created_at, updated_at
                FROM users
                WHERE email = $1
                """,
                email
            )
            if result:
                return UserDB(**dict(result))
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[UserDB]:
        """Get user by ID."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT id, username, email, password_hash, full_name, is_active, is_admin, created_at, updated_at
                FROM users
                WHERE id = $1
                """,
                user_id
            )
            if result:
                return UserDB(**dict(result))
            return None

    async def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[UserDB]:
        """Update user information."""
        update_fields = {}
        if user_update.username is not None:
            update_fields["username"] = user_update.username
        if user_update.email is not None:
            update_fields["email"] = user_update.email
        if user_update.full_name is not None:
            update_fields["full_name"] = user_update.full_name
        if user_update.is_active is not None:
            update_fields["is_active"] = user_update.is_active

        if not update_fields:
            # No fields to update
            return await self.get_user_by_id(user_id)

        # Build update query
        set_clauses = []
        values = []
        param_index = 1
        
        for key, value in update_fields.items():
            set_clauses.append(f"{key} = ${param_index}")
            values.append(value)
            param_index += 1
        
        values.append(datetime.utcnow())  # For updated_at
        values.append(user_id)  # For WHERE clause
        
        query = f"""
            UPDATE users
            SET {', '.join(set_clauses)}, updated_at = ${param_index}
            WHERE id = ${param_index + 1}
            RETURNING id, username, email, password_hash, full_name, is_active, is_admin, created_at, updated_at
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, *values)
            if result:
                return UserDB(**dict(result))
            return None

    async def create_api_key(
        self, user_id: int, key_name: str, api_key: str, expires_at: Optional[datetime] = None
    ) -> APIKeyResponse:
        """Create a new API key for a user."""
        async with self.pool.acquire() as conn:
            now = datetime.utcnow()
            result = await conn.fetchrow(
                """
                INSERT INTO api_keys (user_id, key_name, api_key, expires_at, created_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, key_name, api_key, is_active, expires_at, created_at
                """,
                user_id,
                key_name,
                api_key,
                expires_at,
                now
            )
            return APIKeyResponse(**dict(result))

    async def get_api_key(self, api_key: str) -> Optional[dict]:
        """Get API key details."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT id, user_id, key_name, api_key, is_active, expires_at, created_at, last_used_at
                FROM api_keys
                WHERE api_key = $1
                """,
                api_key
            )
            if result:
                return dict(result)
            return None

    async def verify_api_key(self, api_key: str) -> Optional[int]:
        """Verify an API key and return the user_id if valid."""
        key_data = await self.get_api_key(api_key)
        if not key_data:
            return None
        
        if not key_data["is_active"]:
            return None
        
        if key_data["expires_at"] and key_data["expires_at"] < datetime.utcnow():
            return None
        
        # Update last used timestamp
        await self.update_api_key_usage(key_data["id"])
        return key_data["user_id"]

    async def update_api_key_usage(self, key_id: int) -> None:
        """Update the last_used_at timestamp for an API key."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE api_keys
                SET last_used_at = $1
                WHERE id = $2
                """,
                datetime.utcnow(),
                key_id
            )

# Factory function to get a UserRepository instance
async def get_user_repository():
    pool = await get_db_pool()
    return UserRepository(pool)
