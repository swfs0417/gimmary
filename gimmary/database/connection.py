from typing import AsyncGenerator, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from gimmary.database.settings import DB_SETTINGS


class DatabaseManager:
    def __init__(self):
      self.engine = create_async_engine(
        DB_SETTINGS.url,
        pool_recycle=28000,
        pool_size=10,
        pool_pre_ping=True,
      )
      self.session_factory = async_sessionmaker(
        bind=self.engine, expire_on_commit=False
      )

async def get_db_session() -> AsyncGenerator[AsyncSession, Any]:
    session = DatabaseManager().session_factory()
    try:
      yield session
      await session.commit()
    except Exception as e:
      await session.rollback()
      raise e
    finally:
      await session.close()