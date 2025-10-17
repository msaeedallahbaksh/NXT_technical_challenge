"""
Database configuration and session management.

This module handles async database connections using SQLModel and PostgreSQL.
"""

import os
from typing import AsyncGenerator

from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/assistant"
)

# Create async engine
engine: AsyncEngine = AsyncEngine(
    create_engine(DATABASE_URL, echo=os.getenv("SQL_ECHO", "false").lower() == "true")
)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from models import Product, SessionContext, SearchContext, CartItem
        
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()