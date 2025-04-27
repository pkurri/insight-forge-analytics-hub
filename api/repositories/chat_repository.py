"""
Chat Repository Module

This module provides database operations for chat functionality.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from api.config.database import get_db_session
from api.config.redis_config import get_redis_client
import json
import pickle
from api.config.settings import get_settings

# Get settings
settings = get_settings()
logger = logging.getLogger(__name__)

class ChatRepository:
    """Repository for chat-related database operations."""
    
    def __init__(self):
        """Initialize the repository with database and Redis connection."""
        self.redis = get_redis_client()
        self.cache_ttl = 3600  # Cache TTL in seconds
    
    async def _get_cache_key(self, key_type: str, key_id: str) -> str:
        """Generate cache key."""
        return f"chat:{key_type}:{key_id}"

    async def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all chat sessions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of chat sessions
        """
        try:
            # Check cache first
            cache_key = await self._get_cache_key("user_sessions", str(user_id))
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

            # Query database
            async with get_db_session() as session:
                result = await session.execute(
                    text("""
                    SELECT * FROM chat_sessions 
                    WHERE user_id = :user_id
                    ORDER BY updated_at DESC
                    """),
                    {"user_id": user_id}
                )
                sessions = [dict(row) for row in result]

                # Cache the result
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(sessions)
                )
                return sessions
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific chat session by ID.
        
        Args:
            session_id: ID of the chat session
            
        Returns:
            Chat session data if found, None otherwise
        """
        try:
            # Check cache first
            cache_key = await self._get_cache_key("session", session_id)
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

            # Query database
            async with get_db_session() as session:
                result = await session.execute(
                    text("""
                    SELECT * FROM chat_sessions 
                    WHERE id = :session_id
                    """),
                    {"session_id": session_id}
                )
                row = result.first()
                if row:
                    session_data = dict(row)
                    # Cache the result
                    await self.redis.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(session_data)
                    )
                    return session_data
                return None
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            raise
    
    async def create_session(self, session: Dict[str, Any]) -> None:
        """
        Create a new chat session.
        
        Args:
            session: Chat session data to create
        """
        try:
            async with get_db_session() as db_session:
                await db_session.execute(
                    text("""
                    INSERT INTO chat_sessions 
                    (id, title, user_id, created_at, updated_at, messages)
                    VALUES (:id, :title, :user_id, :created_at, :updated_at, :messages)
                    """),
                    {
                        "id": session["id"],
                        "title": session["title"],
                        "user_id": session["user_id"],
                        "created_at": session["created_at"],
                        "updated_at": session["updated_at"],
                        "messages": json.dumps(session["messages"])
                    }
                )
                await db_session.commit()

            # Invalidate cache
            cache_key = await self._get_cache_key("user_sessions", str(session["user_id"]))
            await self.redis.delete(cache_key)
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    async def update_session(self, session_id: str, session: Dict[str, Any]) -> None:
        """
        Update a chat session.
        
        Args:
            session_id: ID of the chat session to update
            session: Updated chat session data
        """
        try:
            async with get_db_session() as db_session:
                await db_session.execute(
                    text("""
                    UPDATE chat_sessions 
                    SET title = :title,
                        updated_at = :updated_at,
                        messages = :messages
                    WHERE id = :id
                    """),
                    {
                        "id": session_id,
                        "title": session["title"],
                        "updated_at": session["updated_at"],
                        "messages": json.dumps(session["messages"])
                    }
                )
                await db_session.commit()

            # Invalidate cache
            session_cache_key = await self._get_cache_key("session", session_id)
            user_cache_key = await self._get_cache_key("user_sessions", str(session["user_id"]))
            await self.redis.delete(session_cache_key)
            await self.redis.delete(user_cache_key)
        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
            raise
    
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a chat session.
        
        Args:
            session_id: ID of the chat session to delete
        """
        try:
            # Get session first for cache invalidation
            session = await self.get_session(session_id)
            if session:
                async with get_db_session() as db_session:
                    await db_session.execute(
                        text("DELETE FROM chat_sessions WHERE id = :id"),
                        {"id": session_id}
                    )
                    await db_session.commit()

                # Invalidate cache
                session_cache_key = await self._get_cache_key("session", session_id)
                user_cache_key = await self._get_cache_key("user_sessions", str(session["user_id"]))
                await self.redis.delete(session_cache_key)
                await self.redis.delete(user_cache_key)
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            raise
