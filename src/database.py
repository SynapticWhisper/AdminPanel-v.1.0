from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

from src.settings import settings

DATABASE_URL = settings.db_url

Base: DeclarativeMeta = declarative_base()

engine = create_async_engine(DATABASE_URL)
sessionmaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session
