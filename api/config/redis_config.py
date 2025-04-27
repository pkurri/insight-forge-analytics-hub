"""
Redis Configuration Module

This module provides Redis client configuration and connection management.
"""

import aioredis
from api.config.settings import get_settings

settings = get_settings()

async def get_redis_client():
    """Get Redis client instance."""
    redis = await aioredis.create_redis_pool(
        f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}',
        password=settings.REDIS_PASSWORD,
        encoding='utf-8'
    )
    return redis

async def close_redis_connection(redis):
    """Close Redis connection."""
    if redis:
        redis.close()
        await redis.wait_closed()
