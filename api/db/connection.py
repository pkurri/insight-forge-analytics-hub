from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from api.config.settings import get_settings

settings = get_settings()

# Create async engine using the project's DB settings with optimized connection pooling
DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=20,               # Maximum connections in pool
    max_overflow=10,            # Maximum overflow connections
    pool_timeout=30,            # Connection timeout in seconds
    pool_recycle=1800,          # Recycle connections after 30 minutes
    pool_pre_ping=True          # Verify connections before use
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

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
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        import logging
        logging.error(f"Database connection check failed: {str(e)}")
        return False

async def get_connection_stats():
    """
    Get statistics about the connection pool.
    """
    return {
        "pool_size": engine.pool.size(),
        "checkedin": engine.pool.checkedin(),
        "checkedout": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "status": "healthy" if await check_db_connection() else "unhealthy"
    }
