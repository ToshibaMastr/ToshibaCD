from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from ..core import config
from .base_class import Base

engine = create_async_engine(config.DATABASE_URL, pool_size=20, max_overflow=20)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS game_servers"))
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(e)
        raise
