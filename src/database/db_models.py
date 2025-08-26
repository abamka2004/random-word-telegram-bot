from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, Boolean
import pathlib
import os

# Настройка БД
root = pathlib.Path(__file__).parent.parent.parent
DB_PATH = os.environ.get('DB_PATH', os.path.join(root, 'random_word.db'))
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"
engine = create_async_engine(DB_URL)

async_session = async_sessionmaker(engine)


class Base(DeclarativeBase, AsyncAttrs):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    subscription_status: Mapped[bool] = mapped_column(Boolean, default=True)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
