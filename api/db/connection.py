import asyncpg
from contextlib import asynccontextmanager
from api.config.settings import get_settings
import logging
from typing import Optional, List, Dict, Any, Tuple
import os
import json

settings = get_settings()
logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None

async def init_db_pool():
    """Initialize the database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            database=os.getenv('DB_NAME', 'insight_forge'),
            min_size=5,
            max_size=20
        )

async def close_db_pool():
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool."""
    if _pool is None:
        await init_db_pool()
    async with _pool.acquire() as connection:
        yield connection

async def execute_query(query: str, *args, **kwargs):
    """Execute a query and return the results."""
    async with get_db_connection() as conn:
        return await conn.fetch(query, *args, **kwargs)
        
async def execute_many(query: str, args_list: List[Tuple]):
    """Execute a query with multiple sets of parameters."""
    async with get_db_connection() as conn:
        return await conn.executemany(query, args_list)
        
async def execute_single(query: str, *args, **kwargs):
    """Execute a query and return a single result."""
    async with get_db_connection() as conn:
        return await conn.fetchrow(query, *args, **kwargs)
        
async def execute_value(query: str, *args, **kwargs):
    """Execute a query and return a single value."""
    async with get_db_connection() as conn:
        return await conn.fetchval(query, *args, **kwargs)
        
async def execute_command(query: str, *args, **kwargs):
    """Execute a command (insert, update, delete) and return the status."""
    async with get_db_connection() as conn:
        return await conn.execute(query, *args, **kwargs)

async def execute_transaction(queries: list):
    """Execute multiple queries in a transaction."""
    async with get_db_connection() as conn:
        async with conn.transaction():
            results = []
            for query, *args in queries:
                results.append(await conn.fetch(query, *args))
            return results

async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create a connection pool for the database.
    Returns an asyncpg.Pool instance.
    """
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                min_size=5,              # Minimum connections in pool
                max_size=20,             # Maximum connections in pool
                command_timeout=30,       # Command timeout in seconds
                max_inactive_connection_lifetime=1800.0  # Recycle connections after 30 minutes
            )
            logger.info("Database connection pool created successfully")
            
            # Set up JSON encoding/decoding for the pool
            await setup_pool_codecs(_pool)
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {str(e)}")
            raise
    return _pool

async def setup_pool_codecs(pool):
    """Set up JSON encoding/decoding for the pool."""
    def _encode_jsonb(value):
        return json.dumps(value)
    
    def _decode_jsonb(value):
        return json.loads(value)
    
    await pool.set_type_codec(
        'jsonb',
        encoder=_encode_jsonb,
        decoder=_decode_jsonb,
        schema='pg_catalog'
    )
    
    await pool.set_type_codec(
        'json',
        encoder=_encode_jsonb,
        decoder=_decode_jsonb,
        schema='pg_catalog'
    )

async def check_db_connection():
    """
    Check if the database connection is healthy.
    Returns True if connection is successful, False otherwise.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

async def get_connection_stats():
    """
    Get statistics about the connection pools.
    """
    stats = {
        "asyncpg": {
            "status": "not_initialized" if _pool is None else "initialized",
            "min_size": _pool._minsize if _pool else 0,
            "max_size": _pool._maxsize if _pool else 0,
            "size": _pool._size if _pool else 0,
            "free": _pool._free.qsize() if _pool else 0
        }
    }
    
    # Add overall health status
    stats["overall_status"] = "healthy" if await check_db_connection() else "unhealthy"
    
    return stats

async def close_db_pools():
    """
    Close all database connection pools.
    Should be called during application shutdown.
    """
    global _pool
    
    # Close asyncpg pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("AsyncPG connection pool closed")
