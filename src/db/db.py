from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel  # , create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from src.config.settings import Config

async_engine = create_async_engine(url=Config.DATABASE_URL, echo=True)


async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore
    Session = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with Session() as session:
        yield session
