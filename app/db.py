from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from .config import settings

class Base(DeclarativeBase):
    pass

ASYNC_DB_URL = (
    f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASS}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    "?charset=utf8mb4"
)

engine = create_async_engine(ASYNC_DB_URL, echo=False, pool_recycle=3600)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

async def init_db():
    """Create tables & set server timezone to UTC."""
    async with engine.begin() as conn:
        from .models import SensorData, MaintenanceHistory  # ensure models are imported
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("SET time_zone = '+00:00';"))
