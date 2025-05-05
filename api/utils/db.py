import asyncpg
from typing import Optional
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import get_settings

settings = get_settings()
_pool: Optional[asyncpg.Pool] = None
logger = logging.getLogger(__name__)

async def get_db_pool() -> asyncpg.Pool:
    """Get a database connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=20
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Error creating database connection pool: {e}")
            raise
    return _pool

async def close_db_pool():
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")

async def execute_query(query: str, *args):
    """Execute a database query."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def execute_transaction(queries: list):
    """Execute multiple queries in a transaction."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            results = []
            for query, args in queries:
                result = await conn.fetch(query, *args)
                results.append(result)
            return results
