"""
Redis Configuration Module

This module provides Redis client configuration and connection management.
"""

import redis.asyncio as redis
from api.config.settings import get_settings

settings = get_settings()

async def get_redis_client():
    """Get Redis client instance."""
    redis_client = await redis.from_url(
        f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}',
        password=settings.REDIS_PASSWORD,
        encoding='utf-8',
        decode_responses=True
    )
    return redis_client

async def close_redis_connection(redis_client):
    """Close Redis connection."""
    if redis_client:
        await redis_client.close()
