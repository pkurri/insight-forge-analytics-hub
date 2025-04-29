"""
Redis Configuration Module

This module provides Redis client configuration and connection management.
"""

import aioredis
from api.config.settings import get_settings

settings = get_settings()

import aioredis
from api.config.settings import get_settings

settings = get_settings()

async def get_redis_client():
    """Get Redis client instance (production-ready)."""
    try:
        redis = await aioredis.create_redis_pool(
            address=(settings.REDIS_HOST, settings.REDIS_PORT),
            password=settings.REDIS_PASSWORD,
            db=getattr(settings, 'REDIS_DB', 0),
            encoding='utf-8',
            minsize=5,  # pool size for production
            maxsize=50
        )
        return redis
    except Exception as e:
        import logging
        logging.error(f"Error connecting to Redis: {e}")
        raise

async def close_redis_connection(redis):
    """Close Redis connection."""
    if redis:
        redis.close()
        await redis.wait_closed()


async def close_redis_connection(redis):
    """Close Redis connection."""
    if redis:
        redis.close()
        await redis.wait_closed()
