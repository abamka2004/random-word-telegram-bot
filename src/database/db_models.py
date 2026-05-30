import os
import pathlib
from typing import Literal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func, text
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Настройка БД
root = pathlib.Path(__file__).parent.parent.parent
DB_PATH = os.path.join(root, "random_word.db")
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DB_URL)
async_session = async_sessionmaker(engine)


class Base(DeclarativeBase, AsyncAttrs):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    subscription_status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"

    charge_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))

    payload: Mapped[str] = mapped_column(String)

    # Статусы: 'success' (выполнено), 'refundable' (ошибка, можно вернуть), 'refunded' (уже вернули)
    status: Mapped[Literal["success", "refundable", "refunded"]] = mapped_column(
        String, default="success"
    )

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


async def init_db() -> None:
    async with engine.begin() as conn:
        # Включаем WAL режим для предотвращения блокировок базы данных при параллельной записи
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.run_sync(Base.metadata.create_all)
