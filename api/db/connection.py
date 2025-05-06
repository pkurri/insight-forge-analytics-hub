import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from api.config.settings import get_settings
import logging
from typing import Optional

settings = get_settings()
logger = logging.getLogger(__name__)

# Global connection pools
_sqlalchemy_engine = None
_asyncpg_pool: Optional[asyncpg.Pool] = None

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

async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create a connection pool for the database.
    Returns an asyncpg.Pool instance.
    """
    global _asyncpg_pool
    if _asyncpg_pool is None:
        try:
            _asyncpg_pool = await asyncpg.create_pool(
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
    return _asyncpg_pool

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
            "status": "not_initialized" if _asyncpg_pool is None else "initialized",
            "min_size": _asyncpg_pool._minsize if _asyncpg_pool else 0,
            "max_size": _asyncpg_pool._maxsize if _asyncpg_pool else 0,
            "size": _asyncpg_pool._size if _asyncpg_pool else 0,
            "free": _asyncpg_pool._free.qsize() if _asyncpg_pool else 0
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
    global _sqlalchemy_engine, _asyncpg_pool
    
    # Close asyncpg pool
    if _asyncpg_pool is not None:
        await _asyncpg_pool.close()
        _asyncpg_pool = None
        logger.info("AsyncPG connection pool closed")
    
    # Close SQLAlchemy engine
    if _sqlalchemy_engine is not None:
        await _sqlalchemy_engine.dispose()
        _sqlalchemy_engine = None
        logger.info("SQLAlchemy engine closed")
