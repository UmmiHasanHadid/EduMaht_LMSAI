from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
from typing import AsyncGenerator

# Synchronous engine (for table creation only)
sync_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args=sync_connect_args,
)

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.database_url_async,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Sync session for admin / seed tasks
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Async session maker (used by FastAPI endpoints)
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session in FastAPI"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
