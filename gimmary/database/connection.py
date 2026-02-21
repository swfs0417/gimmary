from typing import AsyncGenerator, Any
from alembic.migration import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker

from gimmary.database.settings import DB_SETTINGS

# Engine configured from environment (defaults to local SQLite for dev/tests).
ENGINE = create_engine(DB_SETTINGS.url, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False, future=True)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


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

def get_db_session():
    """FastAPI dependency to inject a SQLAlchemy session per request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()