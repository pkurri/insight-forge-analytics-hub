import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from api.config.settings import get_settings
import logging
from typing import Optional
import os

settings = get_settings()
logger = logging.getLogger(__name__)

# Global connection pools
_sqlalchemy_engine = None
_pool: Optional[asyncpg.Pool] = None

def get_sqlalchemy_engine():
    """
    Get or create the SQLAlchemy engine.
    """
    global _sqlalchemy_engine
    if _sqlalchemy_engine is None:
        DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        _sqlalchemy_engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            future=True,
            pool_size=20,               # Maximum connections in pool
            max_overflow=10,            # Maximum overflow connections
            pool_timeout=30,            # Connection timeout in seconds
            pool_recycle=1800,          # Recycle connections after 30 minutes
            pool_pre_ping=True          # Verify connections before use
        )
    return _sqlalchemy_engine

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=get_sqlalchemy_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

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
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {str(e)}")
            raise
    return _pool

@asynccontextmanager
async def get_db_session():
    """
    Async context manager for DB session, use as:
    async with get_db_session() as session:
        ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

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
        "sqlalchemy": {
            "status": "not_initialized" if _sqlalchemy_engine is None else "initialized",
            "pool_size": _sqlalchemy_engine.pool.size() if _sqlalchemy_engine else 0,
            "checkedin": _sqlalchemy_engine.pool.checkedin() if _sqlalchemy_engine else 0,
            "checkedout": _sqlalchemy_engine.pool.checkedout() if _sqlalchemy_engine else 0,
            "overflow": _sqlalchemy_engine.pool.overflow() if _sqlalchemy_engine else 0
        },
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
    global _sqlalchemy_engine, _pool
    
    # Close asyncpg pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("AsyncPG connection pool closed")
    
    # Close SQLAlchemy engine
    if _sqlalchemy_engine is not None:
        await _sqlalchemy_engine.dispose()
        _sqlalchemy_engine = None
        logger.info("SQLAlchemy engine closed")
